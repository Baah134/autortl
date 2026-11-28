`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module TopModule_top (
    input wire clk,
    input wire areset,
    input wire train_valid,
    input wire train_taken,
    output wire [1:0] state
);
    TopModule u_TopModule (
        .clk(clk),
        .areset(areset),
        .train_valid(train_valid),
        .train_taken(train_taken),
        .state(state)
    );
endmodule
