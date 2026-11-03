`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg [3:0] count;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            count     <= 4'b0000;
        end else if (noisy == clean_reg) begin
            count <= 4'b0000;
        end else if (count == 4'b1000) begin
            clean_reg <= noisy;
            count     <= 4'b0000;
        end else begin
            count <= {count[2:0], ~count[3]};
        end
    end
endmodule