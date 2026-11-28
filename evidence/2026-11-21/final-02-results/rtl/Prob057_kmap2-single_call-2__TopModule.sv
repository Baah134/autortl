module TopModule (
    input  wire a,
    input  wire b,
    input  wire c,
    input  wire d,
    output wire out
);

    assign out = (~a & ~d) | (~b & ~c) | (c & d & (a | b));

endmodule
