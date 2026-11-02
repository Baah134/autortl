`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg candidate;
    reg [2:0] count;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            candidate <= 1'b0;
            count <= 3'd0;
        end else if (noisy != candidate) begin
            candidate <= noisy;
            count <= 3'd0;
        end else if (count < 3'd7) begin
            count <= count + 3'd1;
            if (count == 3'd6)
                clean_reg <= candidate;
        end
    end
endmodule