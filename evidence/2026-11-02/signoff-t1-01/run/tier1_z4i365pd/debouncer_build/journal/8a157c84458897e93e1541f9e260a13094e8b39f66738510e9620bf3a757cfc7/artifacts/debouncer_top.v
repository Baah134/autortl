`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg noisy_prev;
    reg [2:0] stability_count;
    wire terminal_count;

    assign clean = clean_reg;
    assign terminal_count = &stability_count;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg       <= 1'b0;
            noisy_prev      <= 1'b0;
            stability_count <= 3'd0;
        end else begin
            if (noisy != noisy_prev) begin
                noisy_prev <= noisy;
                stability_count <= 3'd1;
            end else if (!terminal_count) begin
                stability_count[0] <= ~stability_count[0];
                stability_count[1] <= stability_count[1] ^ stability_count[0];
                stability_count[2] <= stability_count[2] ^ (stability_count[1] & stability_count[0]);
            end else begin
                clean_reg <= noisy;
            end
        end
    end
endmodule