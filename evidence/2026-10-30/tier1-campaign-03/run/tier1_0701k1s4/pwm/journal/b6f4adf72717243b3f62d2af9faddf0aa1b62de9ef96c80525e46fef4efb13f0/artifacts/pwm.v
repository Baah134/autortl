`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [3:0] counter_low;
    reg [3:0] counter_high;

    always @(posedge clk) begin
        if (rst) begin
            counter_low  <= 4'd0;
            counter_high <= 4'd0;
            pwm_out      <= 1'b0;
        end else begin
            counter_low <= counter_low + 4'd1;
            if (counter_low == 4'hF)
                counter_high <= counter_high + 4'd1;
            pwm_out <= ({counter_high, counter_low} < duty);
        end
    end
endmodule