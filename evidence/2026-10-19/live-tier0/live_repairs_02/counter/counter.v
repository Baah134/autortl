`timescale 1ns/1ps
// @latency 0
module counter (
    input  wire        clk,
    input  wire        rst,
    input  wire        enable,
    input  wire        load,
    input  wire [31:0] load_val,
    output reg  [31:0] count,
    output reg         at_zero,
    output reg         below_low,
    output reg         below_mid,
    output reg         below_high,
    output reg         overflow
);
    always @(posedge clk) begin
        if (rst) begin
            count    <= 32'd0;
            overflow <= 1'b0;
        end else if (load) begin
            count    <= load_val;
            overflow <= 1'b0;
        end else if (enable) begin
            if (count == 32'hFFFF_FFFF) begin
                count    <= 32'd0;
                overflow <= 1'b1;
            end else begin
                count    <= count + 32'd1;
                overflow <= 1'b0;
            end
        end
    end

    always @(*) begin
        at_zero    = 1'b0;
        below_low  = 1'b0;
        below_mid  = 1'b0;
        below_high = 1'b0;

        at_zero    = (count == 32'd0);
        below_low  = (count < 32'd100);
        below_mid  = (count < 32'd500);
        below_high = (count < 32'd1000);
    end
endmodule