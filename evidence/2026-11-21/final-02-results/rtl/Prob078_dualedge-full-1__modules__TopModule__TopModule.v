`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire d,
    output wire q
);
    reg sampled_d;

    // This models the required behavior in simulation. Vivado cannot infer
    // a 7-series ODDR from this block. Meeting the hardware contract requires
    // replanning to allow an ODDR instance and a matching simulation model.
    always @(posedge clk or negedge clk) begin
        sampled_d <= d;
    end

    assign q = sampled_d;
endmodule