module TopModule (
    input  clk,
    input  d,
    output q
);

    reg p;
    reg n;

    always @(posedge clk) begin
        p <= d;
    end

    always @(negedge clk) begin
        n <= d;
    end

    assign q = clk ? p : n;

endmodule
