`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [31:0] counter;
    wire [8:0] duty_difference;

    assign duty_difference = {1'b0, duty} - {1'b0, counter[7:0]};

    always @(posedge clk) begin
        if (rst) begin
            counter <= 32'd0;
            pwm_out <= 1'b0;
        end else begin
            if (counter == 32'd255) counter <= 32'd0;
            else counter <= counter + 32'd1;
            pwm_out <= (counter[31:8] == 24'd0) && duty_difference[8];
        end
    end
endmodule