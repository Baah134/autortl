`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [3:0] phase_low;
    reg [3:0] phase_high;

    always @(posedge clk) begin
        if (rst) begin
            phase_low  <= 4'd0;
            phase_high <= 4'd0;
            pwm_out    <= 1'b0;
        end else begin
            phase_low <= phase_low + 4'd1;
            if (phase_low == 4'hf)
                phase_high <= phase_high + 4'd1;
            pwm_out <= ({phase_high, phase_low} < duty);
        end
    end
endmodule