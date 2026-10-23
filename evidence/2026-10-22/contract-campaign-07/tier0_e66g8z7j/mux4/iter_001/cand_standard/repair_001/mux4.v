`timescale 1ns/1ps
module mux4 (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    input  wire [7:0] d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    always @(posedge clk) begin
        if (rst)
            y <= 8'd0;
        else begin
            case (sel)
                2'd0:    y <= a;
                2'd1:    y <= b;
                2'd2:    y <= c;
                default: y <= d;
            endcase
        end
    end
endmodule