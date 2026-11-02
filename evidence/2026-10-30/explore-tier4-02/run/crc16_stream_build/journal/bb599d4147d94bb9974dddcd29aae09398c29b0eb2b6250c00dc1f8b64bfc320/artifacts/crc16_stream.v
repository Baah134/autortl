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

    wire [15:0] next_crc;

    assign in_ready = !out_valid_reg || out_ready;
    assign out_crc = out_crc_reg;
    assign out_last = out_last_reg;
    assign out_valid = out_valid_reg;

    function [15:0] crc16_update;
        input [15:0] state;
        input [7:0] data;
        reg [7:0] f;
        reg g0;
        reg g1;
        reg g2;
        reg g3;
        begin
            f = state[15:8] ^ data;
            g0 = f[7] ^ f[3];
            g1 = f[6] ^ f[2];
            g2 = f[5] ^ f[1];
            g3 = f[4] ^ f[0];

            crc16_update[15] = state[7] ^ g0;
            crc16_update[14] = state[6] ^ g1;
            crc16_update[13] = state[5] ^ g2;
            crc16_update[12] = state[4] ^ f[7] ^ g3;
            crc16_update[11] = state[3] ^ f[6];
            crc16_update[10] = state[2] ^ f[5];
            crc16_update[9]  = state[1] ^ f[4];
            crc16_update[8]  = state[0] ^ g0;
            crc16_update[7]  = f[7] ^ g1;
            crc16_update[6]  = f[6] ^ g2;
            crc16_update[5]  = f[5] ^ g3;
            crc16_update[4]  = f[4];
            crc16_update[3]  = g0;
            crc16_update[2]  = g1;
            crc16_update[1]  = g2;
            crc16_update[0]  = g3;
        end
    endfunction

    assign next_crc = crc16_update(frame_crc, in_data);

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