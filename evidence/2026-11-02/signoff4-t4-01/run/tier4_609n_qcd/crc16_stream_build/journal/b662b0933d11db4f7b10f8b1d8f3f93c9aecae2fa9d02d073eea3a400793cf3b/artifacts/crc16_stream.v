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

    reg [15:0] crc_reg;
    reg start_of_frame;
    reg out_last_reg;
    reg out_valid_reg;

    assign in_ready = !out_valid_reg || out_ready;
    assign out_crc = crc_reg;
    assign out_last = out_last_reg;
    assign out_valid = out_valid_reg;

    wire [15:0] crc_seed;
    wire [7:0] crc_mix;
    wire [15:0] next_crc;

    assign crc_seed = start_of_frame ? 16'hFFFF : crc_reg;
    assign crc_mix = crc_seed[15:8] ^ in_data;

    assign next_crc[15] = crc_seed[7] ^ crc_mix[3];
    assign next_crc[14] = crc_seed[6] ^ crc_mix[2];
    assign next_crc[13] = crc_seed[5] ^ crc_mix[1];
    assign next_crc[12] = crc_seed[4] ^ crc_mix[0] ^ crc_mix[7];
    assign next_crc[11] = crc_seed[3] ^ crc_mix[6];
    assign next_crc[10] = crc_seed[2] ^ crc_mix[5];
    assign next_crc[9]  = crc_seed[1] ^ crc_mix[4];
    assign next_crc[8]  = crc_seed[0] ^ crc_mix[3];
    assign next_crc[7]  = crc_mix[2] ^ crc_mix[7];
    assign next_crc[6]  = crc_mix[1] ^ crc_mix[6];
    assign next_crc[5]  = crc_mix[0] ^ crc_mix[5];
    assign next_crc[4]  = crc_mix[4];
    assign next_crc[3]  = crc_mix[3];
    assign next_crc[2]  = crc_mix[2];
    assign next_crc[1]  = crc_mix[1];
    assign next_crc[0]  = crc_mix[0];

    always @(posedge clk) begin
        if (rst) begin
            crc_reg <= 16'h0000;
            start_of_frame <= 1'b1;
            out_last_reg <= 1'b0;
            out_valid_reg <= 1'b0;
        end else if (in_ready) begin
            if (in_valid) begin
                crc_reg <= next_crc;
                start_of_frame <= in_last;
                out_last_reg <= in_last;
                out_valid_reg <= 1'b1;
            end else if (out_valid_reg && out_ready) begin
                out_valid_reg <= 1'b0;
            end
        end
    end

endmodule

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