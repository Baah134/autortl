`timescale 1ns/1ps
// @latency 0
module debouncer (
    input  wire clk,
    input  wire rst,
    input  wire noisy,
    output wire clean
);

    reg clean_reg;
    reg tracked_value;
    reg [2:0] count;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg     <= 1'b0;
            tracked_value <= 1'b0;
            count         <= 3'd0;
        end else if (noisy != tracked_value) begin
            tracked_value <= noisy;
            count         <= 3'd1;
        end else if (count < 3'd7) begin
            count <= count + 3'd1;
            if (count == 3'd6)
                clean_reg <= noisy;
        end else begin
            clean_reg <= noisy;
        end
    end

endmodule