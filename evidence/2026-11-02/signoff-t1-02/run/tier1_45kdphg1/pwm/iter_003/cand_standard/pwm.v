`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [31:0] counter;
    wire [31:0] incremented_counter;

    assign incremented_counter = counter + 32'd1;

    always @(posedge clk) begin
        if (rst) begin
            counter <= 32'd0;
            pwm_out <= 1'b0;
        end else begin
            counter <= {
                incremented_counter[31:9],
                incremented_counter[8] & (counter != 32'd255),
                incremented_counter[7:0]
            };
            pwm_out <= (counter < {24'd0, duty});
        end
    end
endmodule