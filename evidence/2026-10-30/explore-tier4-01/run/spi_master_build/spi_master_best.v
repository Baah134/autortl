`timescale 1ns/1ps
// @latency 33
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
module spi_master (
    input wire clk,
    input wire rst,
    input wire [7:0] cmd_data,
    input wire cmd_valid,
    output wire cmd_ready,
    output wire [7:0] rsp_data,
    output wire rsp_valid,
    input wire rsp_ready,
    output wire sclk,
    output wire mosi,
    input wire miso,
    output wire cs_n
);
    spi_master_core #( .HALF_PERIOD(2) ) u_spi_master_core (
        .clk(clk),
        .rst(rst),
        .cmd_data(cmd_data),
        .cmd_valid(cmd_valid),
        .cmd_ready(cmd_ready),
        .rsp_data(rsp_data),
        .rsp_valid(rsp_valid),
        .rsp_ready(rsp_ready),
        .sclk(sclk),
        .mosi(mosi),
        .miso(miso),
        .cs_n(cs_n)
    );
endmodule
