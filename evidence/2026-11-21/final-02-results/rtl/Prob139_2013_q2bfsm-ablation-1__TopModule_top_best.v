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
    reg f_state;
    reg g_state;
    reg matched;
    reg aux_hi;
    reg aux_lo;

    wire next_f;
    wire next_g;
    wire next_aux_hi;
    wire next_aux_lo;
    (* keep = "true" *) wire next_matched;

    assign f = f_state;
    assign g = g_state;

    // Before the match, the auxiliary pair encodes startup, empty, 1, and 10
    // as 00, 01, 11, and 10 respectively.
    // These two functions fit the same five-input set for dual-output packing.
    assign next_f      = resetn & ~matched & ~aux_hi & ~aux_lo;
    assign next_aux_hi = resetn & ~matched &
                         ((aux_hi & aux_lo) | (x & (aux_hi | aux_lo)));

    assign next_matched = resetn & (matched | (aux_hi & ~aux_lo & x));

    // After the match, 10 and 01 select the first and second y samples.
    // Both terminal outcomes use 00 and retain their result in g_state.
    assign next_aux_lo = resetn & (matched ? (aux_hi & ~y)
                                          : (~aux_hi | ~(aux_lo ^ x)));
    assign next_g = next_matched & (~matched | (g_state & (~aux_lo | y)));

    // All next-state functions include the active-low synchronous reset.
    always @(posedge clk) begin
        f_state <= next_f;
        g_state <= next_g;
        matched <= next_matched;
        aux_hi  <= next_aux_hi;
        aux_lo  <= next_aux_lo;
    end
endmodule