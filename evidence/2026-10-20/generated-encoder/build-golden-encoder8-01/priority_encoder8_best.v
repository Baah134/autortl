`timescale 1ns/1ps
module priority_encoder8 (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);
    reg [2:0] index_reg;
    reg valid_reg;
    reg [2:0] index_next;

    wire group_hi4 = |request[7:4];
    wire group_hi2 = |request[7:6];
    wire group_lo4 = |request[3:0];
    wire group_lo2 = |request[3:2];

    assign index = index_reg;
    assign valid = valid_reg;

    always @(*) begin
        index_next = 3'b000;

        if (group_hi4) begin
            index_next[2] = 1'b1;
            index_next[1] = group_hi2;
            index_next[0] = request[7] | (~group_hi2 & request[5]);
        end else if (group_lo4) begin
            index_next[1] = group_lo2;
            index_next[0] = request[3] | (~group_lo2 & request[1]);
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            index_reg <= 3'b000;
            valid_reg <= 1'b0;
        end else begin
            index_reg <= index_next;
            valid_reg <= (request != 8'd0);
        end
    end
endmodule