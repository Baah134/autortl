module TopModule (
    input  wire x,
    input  wire y,
    output wire z
);

    wire z_a1, z_a2;
    wire z_b1, z_b2;

    // Module A: z = (x ^ y) & x
    assign z_a1 = (x ^ y) & x;
    assign z_a2 = (x ^ y) & x;

    // Module B truth table derived from waveform:
    // (x=0, y=0) -> z=1
    // (x=1, y=0) -> z=0
    // (x=0, y=1) -> z=0
    // (x=1, y=1) -> z=1
    // This is equivalent to ~(x ^ y) (XNOR)
    assign z_b1 = ~(x ^ y);
    assign z_b2 = ~(x ^ y);

    wire or_out;
    wire and_out;

    assign or_out  = z_a1 | z_b1;
    assign and_out = z_a2 & z_b2;

    assign z = or_out ^ and_out;

endmodule
