module TopModule (
    input  wire clk,
    input  wire d,
    output wire q
);

    reg q_pos;
    reg q_neg;

    always @(posedge clk) begin
        q_pos <= d ^ q_neg;
    end

    always @(negedge clk) begin
        q_neg <= d ^ q_pos;
    end

    assign q = q_pos ^ q_neg;

endmodule
