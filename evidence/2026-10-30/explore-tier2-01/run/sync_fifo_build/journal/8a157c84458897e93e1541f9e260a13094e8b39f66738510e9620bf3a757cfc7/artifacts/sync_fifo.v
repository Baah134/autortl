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

    reg [7:0] head;
    reg [7:0] middle;
    reg [7:0] tail;
    reg [1:0] occupancy;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = (occupancy < 3) || out_ready;
    assign out_data = head;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 0;
        end else begin
            case ({push, pop})
                2'b10: begin
                    case (occupancy)
                        0: head <= in_data;
                        1: middle <= in_data;
                        2: tail <= in_data;
                        default: begin end
                    endcase
                    occupancy <= occupancy + 1'b1;
                end

                2'b01: begin
                    if (occupancy > 1)
                        head <= middle;
                    if (occupancy > 2)
                        middle <= tail;
                    occupancy <= occupancy - 1'b1;
                end

                2'b11: begin
                    case (occupancy)
                        1: head <= in_data;
                        2: begin
                            head <= middle;
                            middle <= in_data;
                        end
                        3: begin
                            head <= middle;
                            middle <= tail;
                            tail <= in_data;
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