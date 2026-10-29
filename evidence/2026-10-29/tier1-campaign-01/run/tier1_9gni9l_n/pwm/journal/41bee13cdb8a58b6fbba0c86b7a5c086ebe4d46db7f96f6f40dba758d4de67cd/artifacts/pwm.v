`timescale 1ns/1ps
// Deliberately loose PWM: 8-bit counter for an 8-bit duty task.
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [7:0] counter;

    always @(posedge clk) begin
        if (rst) begin
            counter <= 8'd0;
            pwm_out <= 1'b0;
        end else begin
            counter <= counter + 8'd1;
            pwm_out <= (counter < duty);
        end
    end
endmodule