`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg [2:0] lfsr;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            lfsr <= 3'b000;
        end else if (noisy == clean_reg) begin
            lfsr <= 3'b000;
        end else if (lfsr == 3'b000) begin
            lfsr <= 3'b001;
        end else if (lfsr == 3'b010) begin
            clean_reg <= noisy;
            lfsr <= 3'b000;
        end else begin
            lfsr <= {lfsr[2] ^ lfsr[0], lfsr[2:1]};
        end
    end
endmodule