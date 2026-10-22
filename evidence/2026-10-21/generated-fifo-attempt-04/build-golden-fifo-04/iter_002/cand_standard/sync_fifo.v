`timescale 1ns/1ps
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
    reg [7:0] payload0;
    reg [7:0] payload1;
    reg [7:0] payload2;
    reg [1:0] occupancy;
    reg not_full;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready  = not_full || out_ready;
    assign out_data  = payload0;

    assign push = in_valid && in_ready;
    assign pop  = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 0;
            not_full  <= 1'b1;
        end else begin
            case ({push, pop})
                2'b10: begin
                    occupancy <= occupancy + 1'b1;
                    if (occupancy == 2)
                        not_full <= 1'b0;

                    case (occupancy)
                        0: payload0 <= in_data;
                        1: payload1 <= in_data;
                        2: payload2 <= in_data;
                        default: begin
                            payload0 <= payload0;
                            payload1 <= payload1;
                            payload2 <= payload2;
                        end
                    endcase
                end

                2'b01: begin
                    occupancy <= occupancy - 1'b1;
                    if (occupancy == 3)
                        not_full <= 1'b1;

                    payload0 <= payload1;
                    payload1 <= payload2;
                end

                2'b11: begin
                    case (occupancy)
                        1: payload0 <= in_data;
                        2: begin
                            payload0 <= payload1;
                            payload1 <= in_data;
                        end
                        3: begin
                            payload0 <= payload1;
                            payload1 <= payload2;
                            payload2 <= in_data;
                        end
                        default: begin
                            payload0 <= payload0;
                            payload1 <= payload1;
                            payload2 <= payload2;
                        end
                    endcase
                end

                default: begin
                    occupancy <= occupancy;
                    not_full  <= not_full;
                end
            endcase
        end
    end
endmodule