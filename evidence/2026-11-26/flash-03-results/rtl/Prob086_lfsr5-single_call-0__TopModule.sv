module TopModule (
    input  wire       clk,
    input  wire       reset,
    output reg  [4:0] q
);

    always @(posedge clk) begin
        if (reset) begin
            q <= 5'd1;
        end else begin
            // 5-bit Galois LFSR shifting right.
            // Feedback comes from the LSB output bit q[0].
            // Taps are at bit positions 5 and 3 (1-indexed, corresponding to indices 4 and 2).
            // Next state:
            //   q[4] <= q[0] ^ 0 = q[0] (tap at position 5)
            //   q[3] <= q[4]
            //   q[2] <= q[3] ^ q[0]     (tap at position 3)
            //   q[1] <= q[2]
            //   q[0] <= q[1]
            q <= {q[0], q[4], q[3] ^ q[0], q[2], q[1]};
        end
    end

endmodule
