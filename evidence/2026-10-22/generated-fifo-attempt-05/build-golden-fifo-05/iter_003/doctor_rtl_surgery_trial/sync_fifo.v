`timescale 1ns/1ps
// @latency 1
module sync_fifo (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output reg out_valid,
    input wire out_ready
);
    reg [7:0] head;
    reg [7:0] tail_mem [0:1];
    reg tail_rd_ptr;
    reg tail_wr_ptr;
    reg [1:0] occupancy;

    wire push;
    wire pop;

    assign in_ready = (occupancy < 2'd3) || out_ready;
    assign out_data = head;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            tail_rd_ptr <= 1'b0;
            tail_wr_ptr <= 1'b0;
            occupancy <= 2'd0;
            out_valid <= 1'b0;
        end else begin
            case ({push, pop})
                2'b10: begin
                    occupancy <= occupancy + 1'b1;
                    out_valid <= 1'b1;
                    if (occupancy == 2'd0) begin
                        head <= in_data;
                    end else begin
                        tail_mem[tail_wr_ptr] <= in_data;
                        tail_wr_ptr <= ~tail_wr_ptr;
                    end
                end

                2'b01: begin
                    occupancy <= occupancy - 1'b1;
                    if (occupancy == 2'd1)
                        out_valid <= 1'b0;
                    if (occupancy > 2'd1) begin
                        head <= tail_mem[tail_rd_ptr];
                        tail_rd_ptr <= ~tail_rd_ptr;
                    end
                end

                2'b11: begin
                    out_valid <= 1'b1;
                    if (occupancy == 2'd1) begin
                        head <= in_data;
                    end else begin
                        head <= tail_mem[tail_rd_ptr];
                        tail_mem[tail_wr_ptr] <= in_data;
                        tail_rd_ptr <= ~tail_rd_ptr;
                        tail_wr_ptr <= ~tail_wr_ptr;
                    end
                end

                default: begin
                    occupancy <= occupancy;
                end
            endcase
        end
    end
endmodule