`timescale 1ns/1ps
// @latency 0
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire areset,
    input wire predict_valid,
    input wire [6:0] predict_pc,
    output wire predict_taken,
    output wire [6:0] predict_history,
    input wire train_valid,
    input wire train_taken,
    input wire train_mispredicted,
    input wire [6:0] train_history,
    input wire [6:0] train_pc
);
    TopModule u_TopModule (
        .clk(clk),
        .areset(areset),
        .predict_valid(predict_valid),
        .predict_pc(predict_pc),
        .predict_taken(predict_taken),
        .predict_history(predict_history),
        .train_valid(train_valid),
        .train_taken(train_taken),
        .train_mispredicted(train_mispredicted),
        .train_history(train_history),
        .train_pc(train_pc)
    );
endmodule
