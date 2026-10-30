`timescale 1ns/1ps
// @latency 0
module debouncer (
    input  wire clk,
    input  wire rst,
    input  wire noisy,
    output wire clean
);

    reg       candidate;
    reg [3:0] count;
    reg       clean_reg;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            candidate <= 1'b0;
            count     <= 4'd0;
            clean_reg <= 1'b0;
        end else if (noisy != candidate) begin
            candidate <= noisy;
            count     <= 4'd1;
        end else if (count < 4'd8) begin
            count <= count + 1'b1;
            if (count == 4'd7)
                clean_reg <= candidate;
        end
    end

endmodule