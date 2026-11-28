`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg candidate;
    reg [2:0] count;
    reg clean_reg;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            candidate <= 1'b0;
            count     <= 3'd0;
            clean_reg <= 1'b0;
        end else if (noisy != candidate) begin
            candidate <= noisy;
            count     <= 3'd1;
        end else begin
            count <= count + 1'b1;
            if (count == 3'd7)
                clean_reg <= candidate;
        end
    end
endmodule