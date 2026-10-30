`timescale 1ns/1ps
// @latency 1
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
    reg [15:0] frame_crc;
    reg [15:0] out_crc_reg;
    reg out_last_reg;
    reg out_valid_reg;

    wire [15:0] crc_input;
    wire [15:0] next_crc;
    wire f0, f1, f2, f3, f4, f5, f6, f7;

    assign in_ready = !out_valid_reg || out_ready;
    assign out_crc = out_crc_reg;
    assign out_last = out_last_reg;
    assign out_valid = out_valid_reg;

    assign crc_input = frame_crc ^ {in_data, 8'b0};

    assign f0 = crc_input[15];
    assign f1 = crc_input[14];
    assign f2 = crc_input[13];
    assign f3 = crc_input[12] ^ f0;
    assign f4 = crc_input[11] ^ f1;
    assign f5 = crc_input[10] ^ f2;
    assign f6 = crc_input[9] ^ f3;
    assign f7 = crc_input[8] ^ f4;

    assign next_crc[15] = crc_input[7] ^ f4;
    assign next_crc[14] = crc_input[6] ^ f5;
    assign next_crc[13] = crc_input[5] ^ f6;
    assign next_crc[12] = crc_input[4] ^ f7 ^ f0;
    assign next_crc[11] = crc_input[3] ^ f1;
    assign next_crc[10] = crc_input[2] ^ f2;
    assign next_crc[9]  = crc_input[1] ^ f3;
    assign next_crc[8]  = crc_input[0] ^ f4;
    assign next_crc[7]  = f5 ^ f0;
    assign next_crc[6]  = f6 ^ f1;
    assign next_crc[5]  = f7 ^ f2;
    assign next_crc[4]  = f3;
    assign next_crc[3]  = f4;
    assign next_crc[2]  = f5;
    assign next_crc[1]  = f6;
    assign next_crc[0]  = f7;

    always @(posedge clk) begin
        if (rst) begin
            frame_crc <= 16'hFFFF;
            out_valid_reg <= 1'b0;
        end else if (in_valid && in_ready) begin
            out_crc_reg <= next_crc;
            out_last_reg <= in_last;
            out_valid_reg <= 1'b1;
            if (in_last)
                frame_crc <= 16'hFFFF;
            else
                frame_crc <= next_crc;
        end else if (out_valid_reg && out_ready) begin
            out_valid_reg <= 1'b0;
        end
    end
endmodule