`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg [2:0] phase;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            phase <= 3'b000;
        end else if (noisy == clean_reg) begin
            phase <= 3'b000;
        end else begin
            case (phase)
                3'b000: phase <= 3'b001;
                3'b001: phase <= 3'b011;
                3'b011: phase <= 3'b010;
                3'b010: phase <= 3'b110;
                3'b110: phase <= 3'b111;
                3'b111: phase <= 3'b101;
                3'b101: phase <= 3'b100;
                3'b100: begin
                    clean_reg <= noisy;
                    phase <= 3'b000;
                end
                default: phase <= 3'b000;
            endcase
        end
    end
endmodule