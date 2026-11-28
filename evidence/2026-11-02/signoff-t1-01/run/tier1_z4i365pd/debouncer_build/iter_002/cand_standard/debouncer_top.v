`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg [2:0] stability_count;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg       <= 1'b0;
            stability_count <= 3'd0;
        end else if (noisy == clean_reg) begin
            stability_count <= 3'd0;
        end else if (stability_count == 3'd7) begin
            clean_reg       <= noisy;
            stability_count <= 3'd0;
        end else begin
            stability_count <= stability_count + 3'd1;
        end
    end
endmodule