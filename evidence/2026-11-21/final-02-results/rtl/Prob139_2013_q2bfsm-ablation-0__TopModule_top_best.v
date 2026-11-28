`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input wire clk,
    input wire resetn,
    input wire x,
    input wire y,
    output wire f,
    output wire g
);
    // 000 uses f to distinguish reset from the release pulse.
    // 001, 010, and 011 track the empty, 1, and 10 prefixes.
    // 100 samples the first y. 110 and 111 sample the second y.
    // 101 holds the result in g.
    (* fsm_encoding = "none" *) reg [2:0] phase;
    reg f_reg;
    reg g_reg;

    wire post_match;
    wire phase_mid;
    wire phase_low;
    wire first_y;
    wire match_101;
    wire [2:0] next_phase;
    wire next_f;
    wire next_g;

    assign f = f_reg;
    assign g = g_reg;

    assign post_match = phase[2];
    assign phase_mid = phase[1];
    assign phase_low = phase[0];
    assign first_y = ~phase_mid & ~phase_low;
    assign match_101 = phase_mid & phase_low & x;

    assign next_phase[2] = post_match | match_101;
    assign next_phase[1] = post_match ? first_y :
                           ((phase_mid & ~phase_low) |
                            (~phase_mid & (phase_low | f_reg) & x));
    assign next_phase[0] = post_match ? (~first_y | y) :
                           ((phase_mid | phase_low | f_reg) & ~x);

    assign next_f = ~post_match & first_y & ~f_reg;
    assign next_g = post_match ?
                    (phase_low ? (phase_mid | g_reg) : (~phase_mid | y)) :
                    match_101;

    always @(posedge clk) begin
        if (!resetn) begin
            phase <= 3'b000;
            f_reg <= 1'b0;
            g_reg <= 1'b0;
        end else begin
            phase <= next_phase;
            f_reg <= next_f;
            g_reg <= next_g;
        end
    end
endmodule