`timescale 1ns/1ps
// @latency 0
module debouncer (
    input  wire clk,
    input  wire rst,
    input  wire noisy,
    output wire clean
);

    reg clean_reg;
    reg candidate;
    reg [2:0] count;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            candidate <= 1'b0;
            count     <= 3'd0;
        end else if (noisy == candidate) begin
            if (count == 3'd7)
                clean_reg <= candidate;
            else
                count <= count + 1'b1;
        end else begin
            candidate <= noisy;
            count     <= 3'd1;
        end
    end

endmodule