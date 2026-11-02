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
    wire [3:0] stability_sum;

    assign clean = clean_reg;
    assign stability_sum = {1'b0, stability_count} + 4'd1;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg       <= 1'b0;
            stability_count <= 3'd0;
        end else if (noisy == clean_reg) begin
            stability_count <= 3'd0;
        end else begin
            stability_count <= stability_sum[2:0];
            if (stability_sum[3])
                clean_reg <= noisy;
        end
    end
endmodule