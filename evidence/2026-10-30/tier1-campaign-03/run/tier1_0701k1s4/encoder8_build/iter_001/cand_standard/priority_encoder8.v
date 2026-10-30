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
    wire lower_valid;
    wire upper_index1;
    wire lower_index1;
    wire upper_index0;
    wire lower_index0;

    reg [2:0] index_reg;
    reg valid_reg;

    assign upper_valid = |request[7:4];
    assign lower_valid = |request[3:0];

    assign upper_index1 = request[7] | request[6];
    assign lower_index1 = request[3] | request[2];

    assign upper_index0 = request[7] | (~request[6] & request[5]);
    assign lower_index0 = request[3] | (~request[2] & request[1]);

    assign index = index_reg;
    assign valid = valid_reg;

    always @(posedge clk) begin
        if (rst) begin
            index_reg <= 3'd0;
            valid_reg <= 1'b0;
        end else begin
            index_reg[2] <= upper_valid;
            index_reg[1] <= upper_valid ? upper_index1 : lower_index1;
            index_reg[0] <= upper_valid ? upper_index0 : lower_index0;
            valid_reg <= upper_valid | lower_valid;
        end
    end
endmodule