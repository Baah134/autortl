module TopModule (
    input  clk,
    input  d,
    output q
);

    reg p = 1'b0;
    reg n = 1'b0;

    always @(posedge clk) begin
        p <= d ^ n;
    end

    always @(negedge clk) begin
        n <= d ^ p;
    end

    assign q = p ^ n;

endmodule
