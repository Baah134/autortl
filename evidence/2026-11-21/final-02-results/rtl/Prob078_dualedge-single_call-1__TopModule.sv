module TopModule (
    input  wire clk,
    input  wire d,
    output wire q
);
    reg posedge_sample;
    reg negedge_sample;

    always @(posedge clk)
        posedge_sample <= d;

    always @(negedge clk)
        negedge_sample <= d;

    assign q = clk ? posedge_sample : negedge_sample;
endmodule
