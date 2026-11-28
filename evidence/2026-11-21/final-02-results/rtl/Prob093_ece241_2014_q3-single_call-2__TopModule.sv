module TopModule (
    input  wire       c,
    input  wire       d,
    output wire [3:0] mux_in
);
    wire d_bar;

    assign d_bar     = d ? 1'b0 : 1'b1;
    assign mux_in[0] = c ? 1'b1 : d;
    assign mux_in[1] = 1'b0;
    assign mux_in[2] = d ? c : d_bar;
    assign mux_in[3] = c ? d : 1'b0;
endmodule
