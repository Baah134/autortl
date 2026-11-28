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
            // Left neighbor of q[i] is q[i+1], boundary q[512] = 1'b0
            // Right neighbor of q[i] is q[i-1], boundary q[-1] = 1'b0
            // Next state is Left ^ Right
            q <= {1'b0, q[511:1]} ^ {q[510:0], 1'b0};
        end
    end

endmodule
