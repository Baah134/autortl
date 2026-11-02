`timescale 1ns/1ps
// @latency 1
module counter8_core (
    input wire clk,
    input wire rst,
    input wire enable,
    output wire [7:0] count
);

reg [7:0] count_q;
assign count = count_q;

always @(posedge clk) begin
    if (rst)
        count_q <= 8'd0;
    else if (enable)
        count_q <= count_q + 8'd1;
end

endmodule