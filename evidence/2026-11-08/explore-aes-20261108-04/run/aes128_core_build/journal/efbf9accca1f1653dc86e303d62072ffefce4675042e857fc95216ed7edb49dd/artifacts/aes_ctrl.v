`timescale 1ns/1ps
// @latency 1
module aes_ctrl (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [127:0] key,
    input wire [127:0] pt,
    output reg out_valid,
    input wire out_ready,
    output reg [127:0] ct,
    output reg [127:0] rk,
    output wire [7:0] rcon,
    output wire last,
    input wire [127:0] round_out,
    input wire [127:0] key_next
);

    reg busy;
    reg [3:0] rnd;

    assign in_ready = !busy && !out_valid;
    assign last = (rnd == 4'd10);

    assign rcon =
        (rnd == 4'd0)  ? 8'h01 :
        (rnd == 4'd1)  ? 8'h02 :
        (rnd == 4'd2)  ? 8'h04 :
        (rnd == 4'd3)  ? 8'h08 :
        (rnd == 4'd4)  ? 8'h10 :
        (rnd == 4'd5)  ? 8'h20 :
        (rnd == 4'd6)  ? 8'h40 :
        (rnd == 4'd7)  ? 8'h80 :
        (rnd == 4'd8)  ? 8'h1b :
        (rnd == 4'd9)  ? 8'h36 :
                         8'h00;

    always @(posedge clk) begin
        if (rst) begin
            busy      <= 1'b0;
            out_valid <= 1'b0;
            rnd       <= 4'd0;
            ct        <= 128'd0;
            rk        <= 128'd0;
        end else if (busy) begin
            rk <= key_next;
            if (rnd == 4'd0) begin
                rnd <= 4'd1;
            end else begin
                ct <= round_out;
                if (rnd == 4'd10) begin
                    busy      <= 1'b0;
                    out_valid <= 1'b1;
                    rnd       <= 4'd0;
                end else begin
                    rnd <= rnd + 4'd1;
                end
            end
        end else if (out_valid) begin
            if (out_ready)
                out_valid <= 1'b0;
        end else if (in_valid) begin
            ct   <= pt ^ key;
            rk   <= key;
            rnd  <= 4'd0;
            busy <= 1'b1;
        end
    end

endmodule