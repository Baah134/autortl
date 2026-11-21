module TopModule (
    input  wire        clk,
    input  wire        reset,
    input  wire [31:0] in,
    output reg  [31:0] out
);

    reg [31:0] prev_in;

    always @(posedge clk) begin
        prev_in <= in;

        if (reset)
            out <= 32'b0;
        else
            out <= out | (prev_in & ~in);
    end

endmodule
