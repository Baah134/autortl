module TopModule (
    input  wire x,
    input  wire y,
    output wire z
);
    wire a;
    wire b;

    assign a = (x ^ y) & x;
    assign b = ~(x ^ y);
    assign z = (a | b) ^ (a & b);
endmodule
