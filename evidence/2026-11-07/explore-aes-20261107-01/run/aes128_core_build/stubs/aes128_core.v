`timescale 1ns/1ps
module aes128_core (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [127:0] key,
    input wire [127:0] pt,
    output wire out_valid,
    input wire out_ready,
    output wire [127:0] ct
);
    wire [127:0] w_aes_ctrl_ct;
    wire [127:0] w_aes_ctrl_rk;
    wire w_aes_ctrl_last;
    wire [127:0] w_aes_round_state_out;
    wire [7:0] w_aes_ctrl_rcon;
    wire [127:0] w_aes_key_step_key_out;
    assign ct = w_aes_ctrl_ct;
    aes_ctrl u_aes_ctrl (
        .clk(clk),
        .rst(rst),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .key(key),
        .pt(pt),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .ct(w_aes_ctrl_ct),
        .rk(w_aes_ctrl_rk),
        .rcon(w_aes_ctrl_rcon),
        .last(w_aes_ctrl_last),
        .round_out(w_aes_round_state_out),
        .key_next(w_aes_key_step_key_out)
    );
    aes_round u_aes_round (
        .state_in(w_aes_ctrl_ct),
        .round_key(w_aes_ctrl_rk),
        .final_round(w_aes_ctrl_last),
        .state_out(w_aes_round_state_out)
    );
    aes_key_step u_aes_key_step (
        .key_in(w_aes_ctrl_rk),
        .rcon(w_aes_ctrl_rcon),
        .key_out(w_aes_key_step_key_out)
    );
endmodule
