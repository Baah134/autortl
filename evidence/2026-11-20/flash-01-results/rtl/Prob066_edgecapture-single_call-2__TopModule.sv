module TopModule (
    input             clk,
    input             reset,
    input      [31:0] in,
    output reg [31:0] out
);

    reg [31:0] in_dly;

    always @(posedge clk) begin
        in_dly <= in;
        if (reset) begin
            out <= 32'b0;
        end else begin
            out <= out | (in_dly & ~in);
        end
    end

endmodule
