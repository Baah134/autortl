module TopModule (
    input  a,
    input  b,
    input  c,
    input  d,
    output out_sop,
    output out_pos
);

    // Inputs correspond to binary value {a, b, c, d}
    // 1-minterms: 2, 7, 15
    // 0-maxterms: 0, 1, 4, 5, 6, 9, 10, 13, 14
    // Don't-cares: 3, 8, 11, 12

    // Minimum Sum-of-Products (SOP):
    // Grouping m(7) + m(15) = b & c & d
    // Grouping m(2) + d(3) = ~a & ~b & c
    assign out_sop = (b & c & d) | (~a & ~b & c);

    // Minimum Product-of-Sums (POS):
    // 0-cells to cover: 0, 1, 4, 5, 6, 9, 10, 13, 14
    // Combined with don't-cares {3, 8, 11, 12}:
    // Group 1 (cells 0, 1, 4, 5, 8, 9, 12, 13): c = 0 -> term: c
    // Group 2 (cells 0, 1, 2, 3, 8, 9, 10, 11): b = 0 -> contains m(2), not all 0s!
    // Let's find POS directly:
    // ~out:
    // Covers 0s:
    // Cover ~c (covers 0, 1, 4, 5, 8, 9, 12, 13)
    // Remaining 0s: 6 (0110), 10 (1010), 14 (1110)
    // Notice all remaining 0s have c=1 and d=0: {2, 6, 10, 14} is col cd=10.
    // In cd=10: cell 2 is a 1! cell 6 is 0, cell 10 is 0, cell 14 is 0.
    // So cd=10 with cell 2 excluded:
    // Cells 6 (0110), 14 (1110) combine with don't-cares? 6 and 14 form group: b & ~d.
    // Cell 10 (1010) combines with cell 11 (1011, DC), 8 (1000, DC), 12?
    // Cell 10 and 8, 11, 9: a & ~b? But cell 8, 9, 10, 11 -> cell 11 is DC, 10 is 0, 9 is 0, 8 is DC.
    // So a & ~b covers 10 (and 9, 8, 11).
    // Or cell 10 (1010) and 14 (1110) gives a & c & ~d.
    // Let's check maxterms (sum terms):
    // For out_pos:
    // To cover 0s with maxterms:
    // Term 1: c (zeros when c=0, covering 0, 1, 4, 5, 9, 13 and DCs 8, 12)
    // Left uncovered 0s: 6 (0110), 10 (1010), 14 (1110).
    // Group covering 6 and 14: (~b | d) covers when b=1 and d=0 (cells 4, 5, 6, 7? No: b=1, d=0 are cells 4, 6, 12, 14).
    // When b=1, d=0: cells 4, 6, 12, 14 are all 0 or DC. So (~b | d) is a valid maxterm!
    // Group covering 10:
    // Cells with a=1, b=0: 8, 9, 10, 11 (all 0 or DC).
    // Corresponding maxterm: (~a | b).
    // Alternatively, cells with c=1, d=0, a=1: 10, 14. Maxterm: (~a | ~c | d).
    // But (~a | b) has only 2 literals!
    // Let's check (~a | b): when a=1 and b=0, term is 0. Cells 8, 9, 10, 11.
    // None of these are 1 (1-cells are 2, 7, 15). So (~a | b) is valid!
    // Remaining: cell 6 (0110). Covered by (~b | d) (since b=1, d=0).
    // Cells 6 and 14 covered by (~b | d).
    // Cell 10 covered by (~a | b).
    // All 0-cells covered:
    // c covers 0, 1, 4, 5, 9, 13
    // (~b | d) covers 4, 6, 12, 14
    // (~a | b) covers 8, 9, 10, 11
    // Total product of sums: c & (~b | d) & (~a | b)
    // Check 1-cells:
    // 2 (0010): c=1, (~b|d)=1|0=1, (~a|b)=1|0=1 -> out = 1*1*1 = 1. Correct!
    // 7 (0111): c=1, (~b|d)=0|1=1, (~a|b)=1|1=1 -> out = 1*1*1 = 1. Correct!
    // 15 (1111): c=1, (~b|d)=0|1=1, (~a|b)=0|1=1 -> out = 1*1*1 = 1. Correct!
    // Check 0-cells:
    // 0: c=0 -> 0
    // 1: c=0 -> 0
    // 4: c=0 -> 0
    // 5: c=0 -> 0
    // 6: c=1, (~b|d)=0 -> 0
    // 9: c=0 -> 0
    // 10: c=1, (~b|d)=1, (~a|b)=0 -> 0
    // 13: c=0 -> 0
    // 14: c=1, (~b|d)=0 -> 0
    // Can we cover with fewer literals or terms?
    // We have 3 terms, 5 literals: c & (~b | d) & (~a | b).
    // Can we combine (~b | d) and (~a | b)?
    // No, 6 is 0110, 10 is 1010. They differ in two variables (a and b).
    // Thus minimum POS is c & (~a | b) & (~b | d).

    assign out_pos = c & (~a | b) & (~b | d);

endmodule
