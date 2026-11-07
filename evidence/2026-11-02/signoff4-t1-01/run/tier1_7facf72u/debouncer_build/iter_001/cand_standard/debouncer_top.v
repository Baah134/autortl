`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg       clean_reg;
    reg       candidate;
    reg [2:0] state;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            candidate <= 1'b0;
            state     <= 3'b000;
        end else if ((state == 3'b000) || (noisy != candidate)) begin
            candidate <= noisy;
            state     <= 3'b001;
        end else if (state == 3'b100) begin
            clean_reg <= candidate;
        end else begin
            case (state)
                3'b001: state <= 3'b011;
                3'b011: state <= 3'b111;
                3'b111: state <= 3'b110;
                3'b110: state <= 3'b101;
                3'b101: state <= 3'b010;
                3'b010: state <= 3'b100;
                default: state <= 3'b001;
            endcase
        end
    end
endmodule