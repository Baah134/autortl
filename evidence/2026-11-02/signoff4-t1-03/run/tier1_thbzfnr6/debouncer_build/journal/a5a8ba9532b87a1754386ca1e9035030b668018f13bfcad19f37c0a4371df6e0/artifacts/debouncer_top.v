`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg [2:0] run_count;
    reg clean_reg;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            run_count <= 3'b111;
            clean_reg <= 1'b0;
        end else if (noisy == clean_reg) begin
            run_count <= 3'b111;
        end else if (run_count == 3'b000) begin
            clean_reg <= noisy;
            run_count <= 3'b111;
        end else begin
            run_count <= run_count - 3'd1;
        end
    end
endmodule