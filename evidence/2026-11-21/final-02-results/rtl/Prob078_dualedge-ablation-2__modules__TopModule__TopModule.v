`timescale 1ns/1ps
// @latency 1
// The two edge registers model the requested sampling behavior.
// Vivado 7-series does not infer a single ODDR from this RTL.
// Meeting the direct ODDR and zero-fabric requirements requires
// permitting an ODDR instance and providing a simulation model.
module TopModule (
    input  wire clk,
    input  wire d,
    output wire q
);

    reg rising_sample;
    reg falling_sample;

    always @(posedge clk) begin
        rising_sample <= d;
    end

    always @(negedge clk) begin
        falling_sample <= d;
    end

    assign q = clk ? rising_sample : falling_sample;

endmodule