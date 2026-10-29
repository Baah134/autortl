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
    reg [2:0] count;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg     <= 1'b0;
            previous_noisy <= 1'b0;
            count          <= 3'd0;
        end else begin
            previous_noisy <= noisy;

            if (noisy != previous_noisy) begin
                count <= 3'd1;
            end else if (count == 3'd7) begin
                clean_reg <= noisy;
            end else begin
                count <= count + 3'd1;
            end
        end
    end

endmodule