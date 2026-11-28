`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire d,
    output wire q
);
    reg rising_sample;
    reg falling_sample;

    always @(posedge clk)
        rising_sample <= d;

    always @(negedge clk)
        falling_sample <= d;

    // Vivado implements this behavioral DDR circuit in fabric.
    // The dedicated ODDR and zero-LUT target require an ODDR instance.
    assign q = clk ? rising_sample : falling_sample;
endmodule