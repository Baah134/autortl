`timescale 1ns/1ps
// @latency 1
module priority_encoder8_core (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);

reg [2:0] index_reg;
reg valid_reg;

assign index = index_reg;
assign valid = valid_reg;

always @(posedge clk) begin
    if (rst) begin
        index_reg <= 3'd0;
        valid_reg <= 1'b0;
    end else begin
        valid_reg <= (request != 8'd0);

        if (request[7])
            index_reg <= 3'd7;
        else if (request[6])
            index_reg <= 3'd6;
        else if (request[5])
            index_reg <= 3'd5;
        else if (request[4])
            index_reg <= 3'd4;
        else if (request[3])
            index_reg <= 3'd3;
        else if (request[2])
            index_reg <= 3'd2;
        else if (request[1])
            index_reg <= 3'd1;
        else
            index_reg <= 3'd0;
    end
end

endmodule