`timescale 1ns/1ps
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
            counter[3:0] <= counter[3:0] + 4'd1;
            if (counter[3:0] == 4'hF)
                counter[7:4] <= counter[7:4] + 4'd1;
            counter[31:8] <= 24'd0;
            pwm_out <= (counter < {24'd0, duty});
        end
    end
endmodule