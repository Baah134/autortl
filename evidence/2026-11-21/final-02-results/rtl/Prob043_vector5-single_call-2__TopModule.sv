module TopModule (
    input  wire        a,
    input  wire        b,
    input  wire        c,
    input  wire        d,
    input  wire        e,
    output wire [24:0] out
);
    wire [4:0] inputs;

    assign inputs = {a, b, c, d, e};
    assign out[24:20] = {5{a}} ~^ inputs;
    assign out[19:15] = {5{b}} ~^ inputs;
    assign out[14:10] = {5{c}} ~^ inputs;
    assign out[9:5]   = {5{d}} ~^ inputs;
    assign out[4:0]   = {5{e}} ~^ inputs;
endmodule
