module TopModule (
    input  c,
    input  d,
    output [3:0] mux_in
);

    // Using 2-to-1 multiplexers (implemented via ternary operators):
    // mux_in[0] for ab = 00: (c | d)
    assign mux_in[0] = c ? 1'b1 : d;

    // mux_in[1] for ab = 01: constant 0
    assign mux_in[1] = 1'b0;

    // mux_in[2] for ab = 10: (~d | c)
    assign mux_in[2] = d ? c : 1'b1;

    // mux_in[3] for ab = 11: (c & d)
    assign mux_in[3] = c ? d : 1'b0;

endmodule
