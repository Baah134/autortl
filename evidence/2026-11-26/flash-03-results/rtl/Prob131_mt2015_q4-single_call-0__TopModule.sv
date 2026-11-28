module TopModule (
    input  wire x,
    input  wire y,
    output wire z
);

    // Module A implements z = (x ^ y) & x
    // Module B implements XNOR: z = ~(x ^ y)
    wire a1 = (x ^ y) & x;
    wire b1 = ~(x ^ y);

    wire a2 = (x ^ y) & x;
    wire b2 = ~(x ^ y);

    wire or_out  = a1 | b1;
    wire and_out = a2 & b2;

    assign z = or_out ^ and_out;

endmodule
