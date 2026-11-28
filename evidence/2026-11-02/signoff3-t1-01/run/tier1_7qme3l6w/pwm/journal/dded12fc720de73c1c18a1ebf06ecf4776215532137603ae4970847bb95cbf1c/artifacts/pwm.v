`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [7:0] counter;
    wire [7:0] toggle;

    assign toggle[0] = 1'b1;

    genvar i;
    generate
        for (i = 1; i < 8; i = i + 1) begin : gen_toggle
            assign toggle[i] = &counter[i-1:0];
        end
    endgenerate

    always @(posedge clk) begin
        if (rst) begin
            counter <= 8'd0;
            pwm_out <= 1'b0;
        end else begin
            counter <= counter ^ toggle;
            pwm_out <= (counter < duty);
        end
    end
endmodule