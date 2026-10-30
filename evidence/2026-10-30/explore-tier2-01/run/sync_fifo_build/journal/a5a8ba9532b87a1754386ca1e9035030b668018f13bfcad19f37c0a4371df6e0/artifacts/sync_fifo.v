`timescale 1ns/1ps
// @latency 1
module sync_fifo (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    wire core_in_ready;
    wire [7:0] core_out_data;
    wire core_out_valid;

    sync_fifo_core #(.WIDTH(8), .DEPTH(3)) u_sync_fifo_core (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_valid(in_valid),
        .in_ready(core_in_ready),
        .out_data(core_out_data),
        .out_valid(core_out_valid),
        .out_ready(out_ready)
    );

    reg [7:0] mem [0:2];
    reg [7:0] head_cache;
    reg [1:0] rd_ptr;
    reg [1:0] wr_ptr;
    reg [1:0] occupancy;

    wire push;
    wire pop;
    reg [7:0] next_head_data;

    assign out_valid = (occupancy != 0);
    assign in_ready = (occupancy < 3) || out_ready;
    assign out_data = head_cache;
    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(*) begin
        next_head_data = 8'b0;
        case (rd_ptr)
            2'd0: next_head_data = mem[1];
            2'd1: next_head_data = mem[2];
            2'd2: next_head_data = mem[0];
            default: next_head_data = mem[0];
        endcase
    end

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= 0;
            wr_ptr <= 0;
            occupancy <= 0;
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                if (wr_ptr == 2)
                    wr_ptr <= 0;
                else
                    wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop) begin
                if (rd_ptr == 2)
                    rd_ptr <= 0;
                else
                    rd_ptr <= rd_ptr + 1'b1;
            end

            case ({push, pop})
                2'b10: begin
                    occupancy <= occupancy + 1'b1;
                    if (occupancy == 0)
                        head_cache <= in_data;
                end
                2'b01: begin
                    occupancy <= occupancy - 1'b1;
                    if (occupancy > 1)
                        head_cache <= next_head_data;
                end
                2'b11: begin
                    if (occupancy == 1)
                        head_cache <= in_data;
                    else if (occupancy > 1)
                        head_cache <= next_head_data;
                end
                default: begin
                    occupancy <= occupancy;
                end
            endcase
        end
    end
endmodule