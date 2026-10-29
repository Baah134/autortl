`timescale 1ns/1ps
module pwm (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] duty,
    output reg        pwm_out
);
    reg [31:0] counter;

    wire [3:0] carry_low;
    wire [3:0] carry_high;
    wire [3:0] increment_low;
    wire [3:0] increment_high;

    CARRY4 carry4_low (
        .CI     (1'b1),
        .CYINIT (1'b0),
        .DI     (4'b0000),
        .S      (counter[3:0]),
        .CO     (carry_low),
        .O      (increment_low)
    );

    CARRY4 carry4_high (
        .CI     (carry_low[3]),
        .CYINIT (1'b0),
        .DI     (4'b0000),
        .S      (counter[7:4]),
        .CO     (carry_high),
        .O      (increment_high)
    );

    always @(posedge clk) begin
        if (rst) begin
            counter <= 32'd0;
            pwm_out <= 1'b0;
        end else begin
            if (counter == 32'd255)
                counter <= 32'd0;
            else
                counter <= {24'd0, increment_high, increment_low};

            pwm_out <= (counter < {24'd0, duty});
        end
    end
endmodule