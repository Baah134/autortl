`timescale 1ns/1ps
// @latency 1
module skid_buffer (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    reg [7:0] head_data;
    reg [7:0] tail_data;
    reg [1:0] occupancy;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 2'd0);
    assign in_ready = (occupancy < 2'd2) || out_ready;
    assign out_data = head_data;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 2'd0;
        end else begin
            case (occupancy)
                2'd0: begin
                    if (push) begin
                        head_data <= in_data;
                        occupancy <= 2'd1;
                    end
                end

                2'd1: begin
                    if (push && pop) begin
                        head_data <= in_data;
                    end else if (push) begin
                        tail_data <= in_data;
                        occupancy <= 2'd2;
                    end else if (pop) begin
                        occupancy <= 2'd0;
                    end
                end

                2'd2: begin
                    if (pop) begin
                        head_data <= tail_data;
                        if (push) begin
                            tail_data <= in_data;
                            occupancy <= 2'd2;
                        end else begin
                            occupancy <= 2'd1;
                        end
                    end
                end

                default: begin
                    occupancy <= 2'd0;
                end
            endcase
        end
    end
endmodule