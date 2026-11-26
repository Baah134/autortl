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
            // Next state is Left ^ Right for each cell.
            // Boundaries q[512] and q[-1] are 0.
            // Left neighbor is q[i+1], Right neighbor is q[i-1].
            // q[511] = 1'b0 ^ q[510]
            // q[i]   = q[i+1] ^ q[i-1]
            // q[0]   = q[1] ^ 1'b0
            q <= {1'b0, q[511:1]} ^ {q[510:0], 1'b0};
        end
    end

endmodule
