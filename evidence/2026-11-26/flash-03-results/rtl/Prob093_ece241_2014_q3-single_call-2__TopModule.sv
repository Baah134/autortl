module TopModule (
    input  c,
    input  d,
    output [3:0] mux_in
);

    // K-map columns correspond to select ab:
    // ab = 00 -> mux_in[0]
    // ab = 01 -> mux_in[1]
    // ab = 10 -> mux_in[2]  (Note: standard indexing ab=2 -> 10, ab=3 -> 11)
    // ab = 11 -> mux_in[3]
    //
    // For ab = 00:
    // cd = 00: 0
    // cd = 01: 1
    // cd = 10: 1
    // cd = 11: 1
    // mux_in[0] = c | d = c ? 1 : d
    //
    // For ab = 01:
    // cd = 00: 0
    // cd = 01: 0
    // cd = 10: 0
    // cd = 11: 0
    // mux_in[1] = 0
    //
    // For ab = 10 (column 10):
    // cd = 00: 1
    // cd = 01: 0
    // cd = 10: 1
    // cd = 11: 1
    // mux_in[2] = (~d) | c = d ? c : 1
    //
    // For ab = 11 (column 11):
    // cd = 00: 0
    // cd = 01: 0
    // cd = 10: 0
    // cd = 11: 1
    // mux_in[3] = c & d = c ? d : 0

    assign mux_in[0] = c ? 1'b1 : d;
    assign mux_in[1] = 1'b0;
    assign mux_in[2] = d ? c : 1'b1;
    assign mux_in[3] = c ? d : 1'b0;

endmodule
