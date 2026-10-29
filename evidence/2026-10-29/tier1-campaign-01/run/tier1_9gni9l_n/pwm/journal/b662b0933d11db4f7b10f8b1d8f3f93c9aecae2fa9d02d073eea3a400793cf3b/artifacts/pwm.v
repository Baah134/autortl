`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output wire       pwm_out
);
    reg [7:0] counter;
    reg       pwm_out_reg;

    assign pwm_out = pwm_out_reg;

    always @(posedge clk) begin
        if (rst) begin
            counter     <= 8'd0;
            pwm_out_reg <= 1'b0;
        end else begin
            if (counter == 8'hff)
                counter <= 8'd0;
            else
                counter <= counter + 8'd1;

            pwm_out_reg <= (counter < duty);
        end
    end
endmodule