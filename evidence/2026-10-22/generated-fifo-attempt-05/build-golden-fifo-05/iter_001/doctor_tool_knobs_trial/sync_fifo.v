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
    reg [7:0] word0;
    reg [7:0] word1;
    reg [7:0] word2;
    reg [1:0] occupancy;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = (occupancy < 3) || out_ready;
    assign out_data = word0;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 0;
        end else begin
            case ({push, pop})
                2'b10: begin
                    case (occupancy)
                        0: word0 <= in_data;
                        1: word1 <= in_data;
                        2: word2 <= in_data;
                        default: begin end
                    endcase
                    occupancy <= occupancy + 1'b1;
                end
                2'b01: begin
                    word0 <= word1;
                    word1 <= word2;
                    occupancy <= occupancy - 1'b1;
                end
                2'b11: begin
                    case (occupancy)
                        1: word0 <= in_data;
                        2: begin
                            word0 <= word1;
                            word1 <= in_data;
                        end
                        3: begin
                            word0 <= word1;
                            word1 <= word2;
                            word2 <= in_data;
                        end
                        default: begin end
                    endcase
                end
                default: begin
                    occupancy <= occupancy;
                end
            endcase
        end
    end
endmodule