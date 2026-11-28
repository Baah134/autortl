`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [31:0] counter;

    wire counter_upper_zero = (counter[31:8] == 24'd0);
    wire terminal_count = counter_upper_zero && (&counter[7:0]);
    wire duty_compare = counter_upper_zero && (counter[7:0] < duty);

    always @(posedge clk) begin
        if (rst) begin
            counter <= 32'd0;
            pwm_out <= 1'b0;
        end else begin
            if (terminal_count)
                counter <= 32'd0;
            else
                counter <= counter + 32'd1;

            pwm_out <= duty_compare;
        end
    end
endmodule