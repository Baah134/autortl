`timescale 1ns/1ps
// @latency 0
module debouncer_top (
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
            count <= 3'b111;
        end else if (noisy == clean_reg) begin
            count <= 3'b111;
        end else begin
            count <= count - 3'd1;
            if (count == 3'b000)
                clean_reg <= noisy;
        end
    end
endmodule