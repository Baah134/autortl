`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg [6:0] history;
    reg clean_reg;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            history  <= 7'b0;
            clean_reg <= 1'b0;
        end else begin
            history <= {history[5:0], noisy};
            if (history == {7{noisy}})
                clean_reg <= noisy;
        end
    end
endmodule