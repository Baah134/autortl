`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [31:0] counter;
    wire [31:0] increment_enable;
    assign increment_enable = {31'd0, (counter != 32'd255)};

    always @(posedge clk) begin
        if (rst) begin
            counter <= 32'd0;
            pwm_out <= 1'b0;
        end else begin
            counter <= (counter + increment_enable) & {32{increment_enable[0]}};
            pwm_out <= (counter < {24'd0, duty});
        end
    end
endmodule