`timescale 1ns/1ps
// @latency 1
module crc16_stream_core (
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

    reg [15:0] frame_crc;
    reg [15:0] out_crc_reg;
    reg out_last_reg;
    reg out_valid_reg;

    wire [15:0] crc_next;

    assign in_ready = !out_valid_reg || out_ready;
    assign out_crc = out_crc_reg;
    assign out_last = out_last_reg;
    assign out_valid = out_valid_reg;
    assign crc_next = crc16_update(frame_crc, in_data);

    function [15:0] crc16_update;
        input [15:0] state;
        input [7:0] data;
        reg [15:0] value;
        integer i;
        begin
            value = state ^ {data, 8'b0};
            for (i = 0; i < 8; i = i + 1) begin
                if (value[15])
                    value = (value << 1) ^ 16'h1021;
                else
                    value = value << 1;
            end
            crc16_update = value;
        end
    endfunction

    always @(posedge clk) begin
        if (rst) begin
            frame_crc <= 16'hFFFF;
            out_valid_reg <= 1'b0;
        end else if (in_valid && in_ready) begin
            out_crc_reg <= crc_next;
            out_last_reg <= in_last;
            out_valid_reg <= 1'b1;
            if (in_last)
                frame_crc <= 16'hFFFF;
            else
                frame_crc <= crc_next;
        end else if (out_valid_reg && out_ready) begin
            out_valid_reg <= 1'b0;
        end
    end

endmodule