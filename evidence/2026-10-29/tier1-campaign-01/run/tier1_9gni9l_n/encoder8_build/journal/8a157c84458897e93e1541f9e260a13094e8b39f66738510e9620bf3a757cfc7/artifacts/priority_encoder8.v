`timescale 1ns/1ps
// @latency 1
module priority_encoder8 (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);
    wire [2:0] index_next;
    wire valid_next;

    assign index_next[2] = |request[7:4];
    assign index_next[1] = request[7] | request[6] |
                           ((~|request[7:4]) & (request[3] | request[2]));
    assign index_next[0] = request[7] |
                           ((~|request[7:6]) & request[5]) |
                           ((~|request[7:4]) & request[3]) |
                           ((~|request[7:2]) & request[1]);
    assign valid_next = (request != 8'd0);

    reg [2:0] index_reg;
    reg valid_reg;

    assign index = index_reg;
    assign valid = valid_reg;

    always @(posedge clk) begin
        if (rst) begin
            index_reg <= 3'd0;
            valid_reg <= 1'b0;
        end else begin
            index_reg <= index_next;
            valid_reg <= valid_next;
        end
    end
endmodule