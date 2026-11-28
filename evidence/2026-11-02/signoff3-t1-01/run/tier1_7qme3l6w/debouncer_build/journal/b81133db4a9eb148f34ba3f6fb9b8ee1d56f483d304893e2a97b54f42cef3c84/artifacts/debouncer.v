`timescale 1ns/1ps
// @latency 0
module debouncer (
    input  wire clk,
    input  wire rst,
    input  wire noisy,
    output wire clean
);

    reg clean_reg;
    reg previous_noisy;
    reg [2:0] stable_count;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg     <= 1'b0;
            previous_noisy <= 1'b0;
            stable_count  <= 3'd0;
        end else if (noisy != previous_noisy) begin
            previous_noisy <= noisy;
            stable_count   <= 3'd1;
        end else if (stable_count != 3'd7) begin
            stable_count <= stable_count + 3'd1;
        end else begin
            clean_reg <= noisy;
        end
    end

endmodule