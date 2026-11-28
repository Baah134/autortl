`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg [2:0] run_count;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            run_count <= 3'd0;
        end else if (noisy == clean_reg) begin
            run_count <= 3'd0;
        end else if (run_count == 3'd7) begin
            clean_reg <= noisy;
            run_count <= 3'd0;
        end else begin
            run_count <= run_count + 1'b1;
        end
    end
endmodule