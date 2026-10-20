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
    reg [1:0] count;

    wire push;
    wire pop;

    assign in_ready = (count > 2'd2) || out_ready;
    assign out_valid = (count != 2'd0);
    assign out_data = data0;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            count <= 2'd0;
        end else begin
            case ({push, pop})
                2'b10: begin
                    if (count == 2'd0)
                        data0 <= in_data;
                    else
                        data1 <= in_data;
                    count <= count + 2'd1;
                end

                2'b01: begin
                    if (count == 2'd2)
                        data0 <= data1;
                    count <= count - 2'd1;
                end

                2'b11: begin
                    if (count == 2'd1)
                        data0 <= in_data;
                    else if (count == 2'd2) begin
                        data0 <= data1;
                        data1 <= in_data;
                    end
                end

                default: begin
                    count <= count;
                end
            endcase
        end
    end

endmodule