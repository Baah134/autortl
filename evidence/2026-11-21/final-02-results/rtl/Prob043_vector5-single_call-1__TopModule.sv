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
    assign out = {
        ({5{a}} ~^ inputs),
        ({5{b}} ~^ inputs),
        ({5{c}} ~^ inputs),
        ({5{d}} ~^ inputs),
        ({5{e}} ~^ inputs)
    };
endmodule
