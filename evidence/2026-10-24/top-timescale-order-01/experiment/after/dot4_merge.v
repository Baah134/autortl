`timescale 1ns/1ps
// @latency 1
module dot4_merge (
    input wire clk,
    input wire rst,
    input wire [16:0] left_sum,
    input wire [16:0] right_sum,
    output wire [17:0] dot_result
);

    reg [17:0] dot_result_reg;

    assign dot_result = dot_result_reg;

    always @(posedge clk) begin
        if (rst)
            dot_result_reg <= 18'b0;
        else
            dot_result_reg <= {1'b0, left_sum} + {1'b0, right_sum};
    end

endmodule