// Example only for a contract that ALREADY requires this two-cycle datapath.
// Not authorization to insert a stage into a fixed-latency design.
// This example has no reset; use only when that matches the contract.
// @latency 2
module pipe_cut #(parameter W = 16) (
    input  wire         clk,
    input  wire [W-1:0] x,
    output reg  [W-1:0] y
);
    reg [W-1:0] mid;
    always @(posedge clk) begin
        mid <= x + (x << 1);   // g(x): stage 1
        y   <= mid * 3;                // f(mid): stage 2
    end
endmodule
