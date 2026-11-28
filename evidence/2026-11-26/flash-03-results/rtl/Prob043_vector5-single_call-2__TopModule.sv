module TopModule (
    input  a,
    input  b,
    input  c,
    input  d,
    input  e,
    output [24:0] out
);

    wire [4:0] in = {a, b, c, d, e};

    assign out = {
        ~in[4] ^ in[4], ~in[4] ^ in[3], ~in[4] ^ in[2], ~in[4] ^ in[1], ~in[4] ^ in[0],
        ~in[3] ^ in[4], ~in[3] ^ in[3], ~in[3] ^ in[2], ~in[3] ^ in[1], ~in[3] ^ in[0],
        ~in[2] ^ in[4], ~in[2] ^ in[3], ~in[2] ^ in[2], ~in[2] ^ in[1], ~in[2] ^ in[0],
        ~in[1] ^ in[4], ~in[1] ^ in[3], ~in[1] ^ in[2], ~in[1] ^ in[1], ~in[1] ^ in[0],
        ~in[0] ^ in[4], ~in[0] ^ in[3], ~in[0] ^ in[2], ~in[0] ^ in[1], ~in[0] ^ in[0]
    };

endmodule
