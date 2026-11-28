`timescale 1ns/1ps
// @latency 1
module aes_ctrl (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [127:0] key,
    input wire [127:0] pt,
    output wire out_valid,
    input wire out_ready,
    output wire [127:0] ct,
    output wire [127:0] rk,
    output wire [7:0] rcon,
    output wire last,
    input wire [127:0] round_out,
    input wire [127:0] key_next
);

    reg busy;
    reg out_valid_reg;
    reg [3:0] rnd;
    reg [127:0] ct_reg;
    reg [127:0] rk_reg;

    assign in_ready = !busy && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign ct = ct_reg;
    assign rk = rk_reg;
    assign last = (rnd == 4'd10);

    reg [7:0] rcon_comb;
    always @(*) begin
        rcon_comb = 8'h00;
        case (rnd)
            4'd0: rcon_comb = 8'h01;
            4'd1: rcon_comb = 8'h02;
            4'd2: rcon_comb = 8'h04;
            4'd3: rcon_comb = 8'h08;
            4'd4: rcon_comb = 8'h10;
            4'd5: rcon_comb = 8'h20;
            4'd6: rcon_comb = 8'h40;
            4'd7: rcon_comb = 8'h80;
            4'd8: rcon_comb = 8'h1b;
            4'd9: rcon_comb = 8'h36;
            default: rcon_comb = 8'h00;
        endcase
    end
    assign rcon = rcon_comb;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b0;
            rnd <= 4'd0;
            ct_reg <= 128'd0;
            rk_reg <= 128'd0;
        end else if (busy) begin
            rk_reg <= key_next;
            if (rnd == 4'd0) begin
                rnd <= 4'd1;
            end else begin
                ct_reg <= round_out;
                if (rnd == 4'd10) begin
                    busy <= 1'b0;
                    out_valid_reg <= 1'b1;
                    rnd <= 4'd0;
                end else begin
                    rnd <= rnd + 4'd1;
                end
            end
        end else if (out_valid_reg) begin
            if (out_ready)
                out_valid_reg <= 1'b0;
        end else if (in_valid) begin
            ct_reg <= pt ^ key;
            rk_reg <= key;
            rnd <= 4'd0;
            busy <= 1'b1;
        end
    end

endmodule