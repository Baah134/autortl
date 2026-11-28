module TopModule (
    input  a,
    input  b,
    input  c,
    input  d,
    output out_sop,
    output out_pos
);

    // Inputs correspond to 4-bit binary {a, b, c, d}:
    // minterms (1): 2, 7, 15
    // maxterms (0): 0, 1, 4, 5, 6, 9, 10, 13, 14
    // don't cares (d): 3, 8, 11, 12
    //
    // K-map for SOP (grouping 1s and don't cares):
    //   Group 1: minterm 2 (0010) combined with d(3)=0011, d(8)=1000? No, 2 and 3 -> ~a & ~b & c.
    //            Can we group 2 with 3, 10, 11? 10 is 0.
    //            d(2, 3): ~a & ~b & c
    //   Group 2: minterms 7 (0111) and 15 (1111) combined with d(3)=0011, d(11)=1011 -> c & d
    //
    // Combining:
    //   out_sop = (c & d) | (~a & ~b & c)
    //
    // K-map for POS (grouping 0s and don't cares):
    //   Zeros at: 0, 1, 4, 5, 6, 9, 10, 13, 14
    //   Don't cares at: 3, 8, 11, 12
    //   ~out:
    //     Group all where c=0: {0, 1, 4, 5, 8, 9, 12, 13} -> ~c
    //     Remaining 0s: 6 (0110), 10 (1010), 14 (1110)
    //     With don't cares and 2? No, 2 is 1.
    //     All remaining 0s have d=0: {6, 10, 14} plus 2 is 1, but wait:
    //     Cells with d=0 and c=1: 2(1), 6(0), 10(0), 14(0).
    //     Can group 6, 14 with 4, 12? (b & ~d) covers 4, 6, 12, 14 (all 0 or X).
    //     Can group 10 with 8, 11, 12? 10 and 8, 14, 12 -> a & ~d covers 8, 10, 12, 14 (all 0 or X).
    //     Wait, let's check ~out directly:
    //     From SOP: out = c & (d | (~a & ~b)) = c & (~a | d) & (~b | d)
    //     Let's verify maxterms with (c) & (~a | d) & (~b | d):
    //       If c = 0: out = 0 (covers 0, 1, 4, 5, 8, 9, 12, 13) -> correct.
    //       If c = 1:
    //         out = (~a | d) & (~b | d) = (d | (~a & ~b))
    //         d = 1:
    //           3 (0011): out = 1 (X)
    //           7 (0111): out = 1 (1)
    //           11 (1011): out = 1 (X)
    //           15 (1111): out = 1 (1)
    //         d = 0:
    //           2 (0010): ~a & ~b = 1 -> out = 1 (1)
    //           6 (0110): out = 0 (0)
    //           10 (1010): out = 0 (0)
    //           14 (1110): out = 0 (0)
    //     Thus POS: c & (~a | d) & (~b | d)

    assign out_sop = (c & d) | (~a & ~b & c);
    assign out_pos = c & (~a | d) & (~b | d);

endmodule
