module TopModule (
    input  wire x,
    input  wire y,
    output wire z
);

    wire a1;
    wire b1;
    wire a2;
    wire b2;

    wire or_out;
    wire and_out;

    // Submodule A: z = (x ^ y) & x
    assign a1 = (x ^ y) & x;
    assign a2 = (x ^ y) & x;

    // Submodule B: XNOR function derived from waveform
    assign b1 = ~(x ^ y);
    assign b2 = ~(x ^ y);

    // Connecting gates
    assign or_out  = a1 | b1;
    assign and_out = a2 & b2;

    assign z = or_out ^ and_out;

endmodule
