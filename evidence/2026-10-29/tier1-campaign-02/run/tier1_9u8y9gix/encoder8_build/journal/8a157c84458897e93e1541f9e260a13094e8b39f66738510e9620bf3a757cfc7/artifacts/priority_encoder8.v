`timescale 1ns/1ps
// @latency 1
module priority_encoder8 (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);
    wire upper_valid;
    wire upper_hi;
    wire lower_hi;
    reg [2:0] index_reg;
    reg valid_reg;

    assign upper_valid = |request[7:4];
    assign upper_hi = |request[7:6];
    assign lower_hi = |request[3:2];

    assign index = index_reg;
    assign valid = valid_reg;

    always @(posedge clk) begin
        if (rst) begin
            index_reg <= 3'd0;
            valid_reg <= 1'b0;
        end else begin
            valid_reg <= upper_valid | (|request[3:0]);
            index_reg[2] <= upper_valid;
            index_reg[1] <= upper_hi |
                            (~upper_valid & (request[3] | request[2]));
            index_reg[0] <= request[7] |
                            (~upper_hi & request[5]) |
                            (~upper_valid & request[3]) |
                            (~upper_valid & ~lower_hi & request[1]);
        end
    end
endmodule