`timescale 1ns/1ps
// Qualification reference only: crc16_stream_tb.v must pass this source and
// fail every mutant in mutants.json. Never configured as a generation seed.
// The top below is byte-identical to the harness's mechanical wrapper.
// @latency 1
module crc16_stream_core (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_last,
    input wire in_valid,
    output wire in_ready,
    output reg [15:0] out_crc,
    output reg out_last,
    output reg out_valid,
    input wire out_ready
);
    // Running CRC of the current frame; 0xFFFF before a frame's first byte.
    reg [15:0] frame_crc;

    // CRC-16/CCITT-FALSE byte update: poly 0x1021, MSB first, no reflection.
    function [15:0] crc_byte;
        input [15:0] crc_in;
        input [7:0] data;
        integer b;
        reg [15:0] c;
        begin
            c = crc_in ^ {data, 8'h00};
            for (b = 0; b < 8; b = b + 1)
                c = c[15] ? ((c << 1) ^ 16'h1021) : (c << 1);
            crc_byte = c;
        end
    endfunction

    wire [15:0] next_crc = crc_byte(frame_crc, in_data);
    wire accept = in_valid && in_ready;
    assign in_ready = !out_valid || out_ready;

    always @(posedge clk) begin
        if (rst) begin
            out_valid <= 1'b0;
            frame_crc <= 16'h0000; // frame_reset
        end else if (accept) begin
            out_crc <= next_crc;
            out_last <= in_last;
            out_valid <= 1'b1;
            frame_crc <= in_last ? 16'hFFFF : next_crc;
        end else if (out_ready) begin
            out_valid <= 1'b0; // retire
        end
    end
endmodule

`timescale 1ns/1ps
// @latency 1
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
module crc16_stream (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_last,
    input wire in_valid,
    output wire in_ready,
    output wire [15:0] out_crc,
    output wire out_last,
    output wire out_valid,
    input wire out_ready
);
    crc16_stream_core u_crc16_stream_core (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_last(in_last),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_crc(out_crc),
        .out_last(out_last),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule
