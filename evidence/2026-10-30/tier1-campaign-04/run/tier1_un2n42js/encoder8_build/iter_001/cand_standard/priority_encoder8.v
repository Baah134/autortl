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
    wire [1:0] upper_index;
    wire [1:0] lower_index;
    wire [2:0] selected_index;
    reg [2:0] index_reg;
    reg valid_reg;

    assign upper_valid = |request[7:4];
    assign lower_valid = |request[3:0];

    assign upper_index[1] = request[7] | request[6];
    assign upper_index[0] = request[7] | (~request[6] & request[5]);
    assign lower_index[1] = request[3] | request[2];
    assign lower_index[0] = request[3] | (~request[2] & request[1]);

    assign selected_index[2] = upper_valid;
    assign selected_index[1] = upper_valid ? upper_index[1] : lower_index[1];
    assign selected_index[0] = upper_valid ? upper_index[0] : lower_index[0];

    assign index = index_reg;
    assign valid = valid_reg;

    always @(posedge clk) begin
        if (rst) begin
            index_reg <= 3'd0;
            valid_reg <= 1'b0;
        end else begin
            index_reg <= selected_index;
            valid_reg <= upper_valid | lower_valid;
        end
    end
endmodule