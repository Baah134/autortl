module TopModule (
    input  x,
    input  y,
    output z
);

    wire a1, b1;
    wire a2, b2;
    wire or_out;
    wire and_out;

    // First pair of A and B submodules connected to an OR gate
    A inst_a1 (
        x,
        y,
        a1
    );

    B inst_b1 (
        x,
        y,
        b1
    );

    // Second pair of A and B submodules connected to an AND gate
    A inst_a2 (
        x,
        y,
        a2
    );

    B inst_b2 (
        x,
        y,
        b2
    );

    assign or_out  = a1 | b1;
    assign and_out = a2 & b2;
    assign z       = or_out ^ and_out;

endmodule
