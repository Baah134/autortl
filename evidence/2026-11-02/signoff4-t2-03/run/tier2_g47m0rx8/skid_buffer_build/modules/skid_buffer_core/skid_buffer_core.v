`timescale 1ns/1ps
// @latency 1
module skid_buffer_core (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);

    reg [7:0] data0;
    reg [7:0] data1;
    reg [1:0] occupancy;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 2'd0);
    assign in_ready = (occupancy < 2'd2) || out_ready;
    assign out_data = data0;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 2'd0;
        end else begin
            case ({push, pop})
                2'b10: begin
                    if (occupancy == 2'd0) begin
                        data0 <= in_data;
                        occupancy <= 2'd1;
                    end else begin
                        data1 <= in_data;
                        occupancy <= 2'd2;
                    end
                end

                2'b01: begin
                    if (occupancy == 2'd2) begin
                        data0 <= data1;
                        occupancy <= 2'd1;
                    end else begin
                        occupancy <= 2'd0;
                    end
                end

                2'b11: begin
                    if (occupancy == 2'd1) begin
                        data0 <= in_data;
                    end else if (occupancy == 2'd2) begin
                        data0 <= data1;
                        data1 <= in_data;
                    end
                end

                default: begin
                end
            endcase
        end
    end

endmodule