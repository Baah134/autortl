`timescale 1ns/1ps
// @latency 1
module packet_fifo (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_last,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_last,
    output wire out_valid,
    input wire out_ready
);
    reg [8:0] head;
    reg [8:0] tail_mem [0:1];
    reg tail_read_ptr;
    reg [1:0] occupancy;
    reg valid_reg;

    wire push;
    wire pop;
    wire tail_write_ptr;

    assign tail_write_ptr = tail_read_ptr ^ (occupancy == 2'd2);

    assign out_valid = valid_reg;
    assign in_ready = (occupancy < 2'd3) || out_ready;
    assign out_data = head[8:1];
    assign out_last = head[0];

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    packet_fifo_core #(.WIDTH(8), .DEPTH(3)) u_packet_fifo_core (
        .clk(clk),
        .rst(1'b0),
        .in_data(8'b0),
        .in_last(1'b0),
        .in_valid(1'b0),
        .in_ready(),
        .out_data(),
        .out_last(),
        .out_valid(),
        .out_ready(1'b0)
    );

    always @(posedge clk) begin
        if (rst) begin
            tail_read_ptr <= 1'b0;
            occupancy <= 2'd0;
            valid_reg <= 1'b0;
        end else begin
            case ({push, pop})
                2'b10: begin
                    if (occupancy == 2'd0)
                        head <= {in_data, in_last};
                    else
                        tail_mem[tail_write_ptr] <= {in_data, in_last};
                    occupancy <= occupancy + 1'b1;
                    valid_reg <= 1'b1;
                end

                2'b01: begin
                    if (occupancy > 2'd1) begin
                        head <= tail_mem[tail_read_ptr];
                        tail_read_ptr <= ~tail_read_ptr;
                        valid_reg <= 1'b1;
                    end else begin
                        valid_reg <= 1'b0;
                    end
                    occupancy <= occupancy - 1'b1;
                end

                2'b11: begin
                    if (occupancy == 2'd1)
                        head <= {in_data, in_last};
                    else begin
                        head <= tail_mem[tail_read_ptr];
                        tail_mem[tail_write_ptr] <= {in_data, in_last};
                        tail_read_ptr <= ~tail_read_ptr;
                    end
                    valid_reg <= 1'b1;
                end

                default: begin
                    occupancy <= occupancy;
                    valid_reg <= valid_reg;
                end
            endcase
        end
    end
endmodule