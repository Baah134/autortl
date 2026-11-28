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

    // Module B: 
    // From waveform:
    // (0,0) -> 1
    // (0,1) -> 0
    // (1,0) -> 0
    // (1,1) -> 1
    // Which is XNOR: ~(x ^ y)
    assign z_b1 = ~(x ^ y);
    assign z_b2 = ~(x ^ y);

    wire or_out  = z_a1 | z_b1;
    wire and_out = z_a2 & z_b2;

    assign z = or_out ^ and_out;

endmodule
