module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [511:0] data,
    output reg  [511:0] q
);

    always @(posedge clk) begin
        if (load) begin
            q <= data;
        end else begin
            // Next state of cell i is q[i+1] ^ q[i-1], with boundaries q[512] = 0 and q[-1] = 0.
            q <= {1'b0, q[511:1]} ^ {q[510:0], 1'b0};
        end
    end

endmodule
