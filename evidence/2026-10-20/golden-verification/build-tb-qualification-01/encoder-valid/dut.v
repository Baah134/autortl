`timescale 1ns/1ps
module priority_encoder8(input clk, rst, input [7:0] request,
                         output reg [2:0] index, output reg valid);
integer bit_number;
reg [2:0] selected;
always @(*) begin
    selected = 0;
    for (bit_number=0; bit_number<8; bit_number=bit_number+1)
        if (request[bit_number]) selected = bit_number;
end
always @(posedge clk) begin
    if (rst) begin index <= 0; valid <= 0; end
    else begin index <= selected; valid <= 1'b1; end
end
endmodule
