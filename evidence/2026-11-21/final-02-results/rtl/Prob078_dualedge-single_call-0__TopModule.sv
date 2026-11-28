module TopModule (
    input  wire clk,
    input  wire d,
    output wire q
);
    reg posedge_state;
    reg negedge_state;

    always @(posedge clk)
        posedge_state <= d ^ negedge_state;

    always @(negedge clk)
        negedge_state <= d ^ posedge_state;

    assign q = posedge_state ^ negedge_state;
endmodule
