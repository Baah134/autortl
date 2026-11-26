module TopModule (
    input  c,
    input  d,
    output [3:0] mux_in
);

    // mux_in[0] corresponds to ab = 00:
    // cd = 00: 0, cd = 01: 1, cd = 11: 1, cd = 10: 1
    // Function: c | d, implemented with a 2-to-1 mux selecting between d (when c=0) and 1 (when c=1)
    // mux_in[0] = c ? 1'b1 : d;

    // mux_in[1] corresponds to ab = 01:
    // cd = 00: 0, cd = 01: 0, cd = 11: 0, cd = 10: 0
    // Function: 0
    // mux_in[1] = 1'b0;

    // mux_in[2] corresponds to ab = 10:
    // Notice the column order in K-map: 00 (mux_in[0]), 01 (mux_in[1]), 11 (mux_in[3]), 10 (mux_in[2])
    // For ab = 10 (mux_in[2]):
    // cd = 00: 1, cd = 01: 0, cd = 11: 1, cd = 10: 1
    // Function: ~d | c, implemented with a 2-to-1 mux selecting between ~d (when c=0) and 1 (when c=1),
    // or c ? 1'b1 : (d ? 1'b0 : 1'b1);

    // mux_in[3] corresponds to ab = 11:
    // cd = 00: 0, cd = 01: 0, cd = 11: 1, cd = 10: 0
    // Function: c & d, implemented with a 2-to-1 mux: c ? d : 1'b0;

    assign mux_in[0] = c ? 1'b1 : d;
    assign mux_in[1] = 1'b0;
    assign mux_in[2] = c ? 1'b1 : (d ? 1'b0 : 1'b1);
    assign mux_in[3] = c ? d : 1'b0;

endmodule
