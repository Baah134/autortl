module TopModule (
    input  c,
    input  d,
    output [3:0] mux_in
);

    // From the K-map:
    // When ab = 00: mux_in[0] = c | d
    //   Implemented using a 2-to-1 mux: c ? 1'b1 : d
    // When ab = 01: mux_in[1] = 1'b0
    // When ab = 10: mux_in[2] = ~d | c
    //   Implemented using a 2-to-1 mux: c ? 1'b1 : ~d
    //   Notice ~d is: d ? 1'b0 : 1'b1
    //   Alternatively: d ? c : 1'b1
    // When ab = 11: mux_in[3] = c & d
    //   Implemented using a 2-to-1 mux: c ? d : 1'b0

    assign mux_in[0] = c ? 1'b1 : d;
    assign mux_in[1] = 1'b0;
    assign mux_in[2] = d ? c : 1'b1;
    assign mux_in[3] = c ? d : 1'b0;

endmodule
