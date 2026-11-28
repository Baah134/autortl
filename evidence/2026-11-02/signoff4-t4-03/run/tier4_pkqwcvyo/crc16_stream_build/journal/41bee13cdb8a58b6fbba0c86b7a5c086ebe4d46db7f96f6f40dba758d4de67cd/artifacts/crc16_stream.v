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

    wire [15:0] crc0;
    wire [15:0] crc1;
    wire [15:0] crc2;
    wire [15:0] crc3;
    wire [15:0] crc4;
    wire [15:0] crc5;
    wire [15:0] crc6;
    wire [15:0] crc7;
    wire [15:0] next_crc;
    wire [15:0] crc_input;
    wire fb0, fb1, fb2, fb3, fb4, fb5, fb6, fb7;

    assign in_ready = !out_valid_reg || out_ready;
    assign out_crc = out_crc_reg;
    assign out_last = out_last_reg;
    assign out_valid = out_valid_reg;

    assign crc_input = frame_crc ^ {in_data, 8'b0};

    assign fb0 = crc_input[15];
    assign crc0 = {crc_input[14:0], 1'b0} ^
                  (fb0 ? 16'h1021 : 16'h0000);
    assign fb1 = crc0[15];
    assign crc1 = {crc0[14:0], 1'b0} ^
                  (fb1 ? 16'h1021 : 16'h0000);
    assign fb2 = crc1[15];
    assign crc2 = {crc1[14:0], 1'b0} ^
                  (fb2 ? 16'h1021 : 16'h0000);
    assign fb3 = crc2[15];
    assign crc3 = {crc2[14:0], 1'b0} ^
                  (fb3 ? 16'h1021 : 16'h0000);
    assign fb4 = crc3[15];
    assign crc4 = {crc3[14:0], 1'b0} ^
                  (fb4 ? 16'h1021 : 16'h0000);
    assign fb5 = crc4[15];
    assign crc5 = {crc4[14:0], 1'b0} ^
                  (fb5 ? 16'h1021 : 16'h0000);
    assign fb6 = crc5[15];
    assign crc6 = {crc5[14:0], 1'b0} ^
                  (fb6 ? 16'h1021 : 16'h0000);
    assign fb7 = crc6[15];
    assign crc7 = {crc6[14:0], 1'b0} ^
                  (fb7 ? 16'h1021 : 16'h0000);
    assign next_crc = crc7;

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