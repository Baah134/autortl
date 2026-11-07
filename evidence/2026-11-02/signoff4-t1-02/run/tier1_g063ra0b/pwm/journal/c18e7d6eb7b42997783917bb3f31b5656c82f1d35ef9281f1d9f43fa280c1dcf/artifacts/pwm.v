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
            counter[0] <= ~counter[0];
            counter[1] <= counter[1] ^ counter[0];
            counter[2] <= counter[2] ^ (&counter[1:0]);
            counter[3] <= counter[3] ^ (&counter[2:0]);
            counter[4] <= counter[4] ^ (&counter[3:0]);
            counter[5] <= counter[5] ^ (&counter[4:0]);
            counter[6] <= counter[6] ^ (&counter[5:0]);
            counter[7] <= counter[7] ^ (&counter[6:0]);
            pwm_out_reg <= (counter < {24'd0, duty});
        end
    end
endmodule