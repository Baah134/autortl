`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg previous_noisy;
    reg [2:0] stable_lfsr;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg     <= 1'b0;
            previous_noisy <= 1'b0;
            stable_lfsr   <= 3'b000;
        end else begin
            previous_noisy <= noisy;

            if (noisy != previous_noisy) begin
                stable_lfsr <= 3'b001;
            end else if (stable_lfsr == 3'b010) begin
                clean_reg <= noisy;
            end else if (stable_lfsr == 3'b000) begin
                stable_lfsr <= 3'b001;
            end else begin
                stable_lfsr <= {stable_lfsr[0] ^ stable_lfsr[1],
                                stable_lfsr[2:1]};
            end
        end
    end
endmodule