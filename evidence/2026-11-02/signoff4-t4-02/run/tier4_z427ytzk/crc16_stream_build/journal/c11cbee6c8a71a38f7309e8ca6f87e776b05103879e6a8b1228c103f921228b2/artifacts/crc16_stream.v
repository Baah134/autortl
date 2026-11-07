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

    wire [15:0] crc_s0;
    wire [15:0] crc_s1;
    wire [15:0] crc_s2;
    wire [15:0] crc_s3;
    wire [15:0] crc_s4;
    wire [15:0] crc_s5;
    wire [15:0] crc_s6;
    wire [15:0] crc_s7;
    wire [15:0] crc_s8;

    assign in_ready = !out_valid_reg || out_ready;
    assign out_crc = out_crc_reg;
    assign out_last = out_last_reg;
    assign out_valid = out_valid_reg;

    assign crc_s0 = frame_crc ^ {in_data, 8'b0};
    assign crc_s1 = {crc_s0[14:0], 1'b0} ^ ({16{crc_s0[15]}} & 16'h1021);
    assign crc_s2 = {crc_s1[14:0], 1'b0} ^ ({16{crc_s1[15]}} & 16'h1021);
    assign crc_s3 = {crc_s2[14:0], 1'b0} ^ ({16{crc_s2[15]}} & 16'h1021);
    assign crc_s4 = {crc_s3[14:0], 1'b0} ^ ({16{crc_s3[15]}} & 16'h1021);
    assign crc_s5 = {crc_s4[14:0], 1'b0} ^ ({16{crc_s4[15]}} & 16'h1021);
    assign crc_s6 = {crc_s5[14:0], 1'b0} ^ ({16{crc_s5[15]}} & 16'h1021);
    assign crc_s7 = {crc_s6[14:0], 1'b0} ^ ({16{crc_s6[15]}} & 16'h1021);
    assign crc_s8 = {crc_s7[14:0], 1'b0} ^ ({16{crc_s7[15]}} & 16'h1021);

    always @(posedge clk) begin
        if (rst) begin
            frame_crc <= 16'hFFFF;
            out_valid_reg <= 1'b0;
        end else if (in_valid && in_ready) begin
            out_crc_reg <= crc_s8;
            out_last_reg <= in_last;
            out_valid_reg <= 1'b1;
            if (in_last)
                frame_crc <= 16'hFFFF;
            else
                frame_crc <= crc_s8;
        end else if (out_valid_reg && out_ready) begin
            out_valid_reg <= 1'b0;
        end
    end

endmodule

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