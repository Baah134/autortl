`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [7:0] phase_n;

    always @(posedge clk) begin
        if (rst) begin
            phase_n <= 8'hFF;
            pwm_out <= 1'b0;
        end else begin
            phase_n <= phase_n - 8'd1;
            pwm_out <= ((~phase_n) < duty);
        end
    end
endmodule