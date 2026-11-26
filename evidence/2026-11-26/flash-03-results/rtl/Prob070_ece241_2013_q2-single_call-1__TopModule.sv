module TopModule (
    input  a,
    input  b,
    input  c,
    input  d,
    output out_sop,
    output out_pos
);

    // Minimum Sum-of-Products (SOP):
    // minterms: 2, 7, 15
    // don't cares: 3, 8, 11, 12
    // Prime implicants covering the minterms:
    // - m(2, 3) -> ~a & ~b & c
    // - m(7, 15) -> b & c & d
    assign out_sop = (~a & ~b & c) | (b & c & d);

    // Minimum Product-of-Sums (POS):
    // maxterms: 0, 1, 4, 5, 6, 9, 10, 13, 14
    // don't cares: 3, 8, 11, 12
    // Covering zeros of f (prime implicants of ~f):
    // ~f = ~c | (~b & d) | (a & ~d)
    // POS = ~(~f):
    // out_pos = c & (b | ~d) & (~a | d)
    assign out_pos = c & (b | ~d) & (~a | d);

endmodule
