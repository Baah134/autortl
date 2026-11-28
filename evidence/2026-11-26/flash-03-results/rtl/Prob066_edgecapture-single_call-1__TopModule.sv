module TopModule (
    input  wire        clk,
    input  wire        reset,
    input  wire [31:0] in,
    output reg  [31:0] out
);

    reg [31:0] in_prev;

    always @(posedge clk) begin
        if (reset) begin
            in_prev <= in;
            out     <= 32'b0;
        end else begin
            in_prev <= in;
            out     <= out | (in_prev & ~in);
        end
    end

endmodule
