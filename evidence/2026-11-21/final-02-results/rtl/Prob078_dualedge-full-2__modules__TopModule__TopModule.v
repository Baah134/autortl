`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire d,
    output wire q
);

    reg rising_data;
    reg falling_data;

    always @(posedge clk)
        rising_data <= d;

    always @(negedge clk)
        falling_data <= d;

    // This preserves both edge captures in RTL simulation after register updates.
    // Vivado implements this as fabric registers and a mux. The mux can expose
    // an old sample during an edge transition. The required direct, zero-LUT
    // ODDR implementation needs a primitive instance, which is prohibited.
    assign q = clk ? rising_data : falling_data;

endmodule