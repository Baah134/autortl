module TopModule (
    input  wire x,
    input  wire y,
    output wire z
);

    wire a1, b1;
    wire a2, b2;
    wire or_out;
    wire and_out;

    assign a1 = (x ^ y) & x;
    assign b1 = ~(x ^ y);

    assign a2 = (x ^ y) & x;
    assign b2 = ~(x ^ y);

    assign or_out  = a1 | b1;
    assign and_out = a2 & b2;

    assign z = or_out ^ and_out;

endmodule
