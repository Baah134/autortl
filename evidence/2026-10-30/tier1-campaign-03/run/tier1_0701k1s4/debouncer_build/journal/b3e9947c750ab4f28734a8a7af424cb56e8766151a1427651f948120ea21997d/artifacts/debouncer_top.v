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
            count     <= 3'b000;
            clean_reg <= 1'b0;
        end else if (noisy != candidate) begin
            candidate <= noisy;
            count     <= 3'b001;
        end else if (count == 3'b100) begin
            clean_reg <= candidate;
        end else begin
            count <= {count[1:0], count[2] ^ count[0]};
        end
    end
endmodule