`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg clean_reg;
    reg [2:0] johnson;
    reg phase;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            clean_reg <= 1'b0;
            johnson <= 3'b000;
            phase <= 1'b0;
        end else if (noisy == clean_reg) begin
            johnson <= 3'b000;
            phase <= 1'b0;
        end else if (phase && (johnson == 3'b001)) begin
            clean_reg <= noisy;
            johnson <= 3'b000;
            phase <= 1'b0;
        end else begin
            case (johnson)
                3'b000: johnson <= 3'b001;
                3'b001: johnson <= 3'b011;
                3'b011: johnson <= 3'b111;
                3'b111: johnson <= 3'b110;
                3'b110: johnson <= 3'b100;
                3'b100: begin
                    johnson <= 3'b000;
                    phase <= 1'b1;
                end
                default: begin
                    johnson <= 3'b000;
                    phase <= 1'b0;
                end
            endcase
        end
    end
endmodule