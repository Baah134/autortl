`timescale 1ns/1ps
// @latency 0
module debouncer (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);

    reg clean_reg;
    reg [2:0] count;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            count <= 3'd0;
        end else if (noisy != clean_reg) begin
            count <= 3'd0;
        end else if (count == 3'd7) begin
            clean_reg <= noisy;
            count <= 3'd0;
        end else begin
            count <= count + 3'd1;
        end
    end

endmodule