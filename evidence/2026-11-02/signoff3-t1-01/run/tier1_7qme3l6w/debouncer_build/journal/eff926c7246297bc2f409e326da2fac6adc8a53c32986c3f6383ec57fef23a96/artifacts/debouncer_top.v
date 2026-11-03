`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    debouncer u_debouncer (
        .clk(clk),
        .rst(rst),
        .noisy(noisy),
        .clean(clean)
    );
endmodule