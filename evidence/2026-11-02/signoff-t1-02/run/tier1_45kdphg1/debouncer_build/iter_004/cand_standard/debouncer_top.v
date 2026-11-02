`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg [3:0] johnson;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            johnson <= 4'b0000;
        end else if (noisy == clean_reg) begin
            johnson <= 4'b0000;
        end else begin
            johnson <= {johnson[2:0], ~johnson[3]};
            if (johnson == 4'b0111)
                clean_reg <= noisy;
        end
    end
endmodule