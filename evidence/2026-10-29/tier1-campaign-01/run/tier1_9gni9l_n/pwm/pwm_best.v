`timescale 1ns/1ps
// Deliberately loose PWM: full 32-bit counter for an 8-bit duty task.
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [31:0] counter;
    always @(posedge clk) begin
        if (rst) begin
            counter <= 32'd0;
            pwm_out <= 1'b0;
        end else begin
            if (counter == 32'd255) counter <= 32'd0;
            else counter <= counter + 32'd1;
            pwm_out <= (counter < {24'd0, duty});
        end
    end
endmodule