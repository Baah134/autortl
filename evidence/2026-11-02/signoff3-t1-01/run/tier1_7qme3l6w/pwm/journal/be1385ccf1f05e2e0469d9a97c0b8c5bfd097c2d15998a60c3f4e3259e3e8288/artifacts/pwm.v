`timescale 1ns/1ps
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
            counter <= counter ^ {
                &counter[6:0],
                &counter[5:0],
                &counter[4:0],
                &counter[3:0],
                &counter[2:0],
                &counter[1:0],
                counter[0],
                1'b1
            };
            pwm_out <= (counter < {24'd0, duty});
        end
    end
endmodule