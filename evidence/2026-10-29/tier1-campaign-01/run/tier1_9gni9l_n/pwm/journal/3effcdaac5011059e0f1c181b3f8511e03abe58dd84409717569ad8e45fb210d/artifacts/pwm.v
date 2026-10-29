`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output wire       pwm_out
);
    reg [7:0] phase;
    reg       pwm_out_reg;

    assign pwm_out = pwm_out_reg;

    always @(posedge clk) begin
        if (rst) begin
            phase       <= 8'hff;
            pwm_out_reg <= 1'b0;
        end else begin
            if (phase == 8'h00)
                phase <= 8'hff;
            else
                phase <= phase - 8'd1;
            pwm_out_reg <= (phase > ~duty);
        end
    end
endmodule