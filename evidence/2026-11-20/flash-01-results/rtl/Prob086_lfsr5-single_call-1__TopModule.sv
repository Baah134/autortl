module TopModule (
    input  wire       clk,
    input  wire       reset,
    output reg  [4:0] q
);

    always @(posedge clk) begin
        if (reset) begin
            q <= 5'd1;
        end else begin
            q <= {q[0], q[4], q[3] ^ q[0], q[2], q[1]};
        end
    end

endmodule
