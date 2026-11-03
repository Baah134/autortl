`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg [2:0] progress;
    reg clean_reg;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            progress <= 3'b000;
            clean_reg <= 1'b0;
        end else if (noisy == clean_reg) begin
            progress <= 3'b000;
        end else begin
            progress[2] <= progress[1];
            progress[1] <= progress[0];
            progress[0] <= (~progress[2] & (progress[1] | ~progress[0])) |
                           (progress[2] & ~progress[1] & progress[0]);

            if (progress == 3'b100)
                clean_reg <= noisy;
        end
    end
endmodule