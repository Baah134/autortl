module TopModule (
    input  a,
    input  b,
    input  c,
    input  d,
    output out
);

    assign out = (~a & ~d) | (~c & ~d) | (~a & ~b & ~c) | (~b & ~c & d) | (a & c & d) | (~a & b & c & d) | (a & ~b & ~c & ~d);

endmodule
