`timescale 1ns/1ps
module uart_rx_fifo (
    input wire clk,
    input wire rst,
    input wire rx,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready,
    output wire frame_err,
    output wire [3:0] ferr_count,
    output wire [3:0] ovf_count
);
    wire w_uart_rx_core_rx_strobe;
    wire [7:0] w_uart_rx_core_rx_data;
    wire w_uart_rx_core_frame_err;
    wire w_rx_fifo_overflow;
    assign frame_err = w_uart_rx_core_frame_err;
    uart_rx_core #( .OVERSAMPLE_DIV(2) ) u_uart_rx_core (
        .clk(clk),
        .rst(rst),
        .rx(rx),
        .rx_data(w_uart_rx_core_rx_data),
        .rx_strobe(w_uart_rx_core_rx_strobe),
        .frame_err(w_uart_rx_core_frame_err)
    );
    rx_fifo #( .ADDR_BITS(2) ) u_rx_fifo (
        .clk(clk),
        .rst(rst),
        .wr_en(w_uart_rx_core_rx_strobe),
        .wr_data(w_uart_rx_core_rx_data),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .overflow(w_rx_fifo_overflow)
    );
    rx_err_count u_rx_err_count (
        .clk(clk),
        .rst(rst),
        .ferr_in(w_uart_rx_core_frame_err),
        .ovf_in(w_rx_fifo_overflow),
        .ferr_count(ferr_count),
        .ovf_count(ovf_count)
    );
endmodule
