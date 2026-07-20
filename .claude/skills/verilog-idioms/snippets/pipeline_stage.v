// Adding one pipeline cut: register the midpoint of a long computation.
// Before: y = f(g(x)) in one cycle. After: two cycles (update // @latency!).
module pipe_cut #(parameter W = 16) (
    input  wire         clk,
    input  wire [W-1:0] x,
    output reg  [W-1:0] y
);
    reg [W-1:0] mid;
    always @(posedge clk) begin
        mid <= x + {x[W-2:0], 1'b0};   // g(x): stage 1
        y   <= mid * 3;                // f(mid): stage 2
    end
endmodule
