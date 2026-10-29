`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [3:0] counter_lo;
    reg [3:0] counter_hi;

    always @(posedge clk) begin
        if (rst) begin
            counter_lo <= 4'd0;
            counter_hi <= 4'd0;
            pwm_out <= 1'b0;
        end else begin
            counter_lo <= counter_lo + 4'd1;
            if (counter_lo == 4'hf)
                counter_hi <= counter_hi + 4'd1;
            pwm_out <= ({counter_hi, counter_lo} < {24'd0, duty});
        end
    end
endmodule