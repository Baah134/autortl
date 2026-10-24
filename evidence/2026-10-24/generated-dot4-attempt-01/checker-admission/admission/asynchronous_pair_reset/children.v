`timescale 1ns/1ps
// Qualification control only; never a generated seed or winner.
// @latency 1
module dot4_pair01(input clk, input rst, input [7:0] a0,b0,a1,b1, output reg [16:0] pair01_sum);
    wire [15:0] product0 = a0 * b0;
    wire [15:0] product1 = a1 * b1;
    always @(posedge clk or posedge rst) begin // pair01_clock
        if(rst) pair01_sum <= 0;
        else pair01_sum <= {1'b0,product0} + {1'b0,product1};
    end
endmodule

// @latency 1
module dot4_pair23(input clk, input rst, input [7:0] a2,b2,a3,b3, output reg [16:0] pair23_sum);
    wire [15:0] product2 = a2 * b2;
    wire [15:0] product3 = a3 * b3;
    always @(posedge clk) begin // pair23_clock
        if(rst) pair23_sum <= 0;
        else pair23_sum <= {1'b0,product2} + {1'b0,product3};
    end
endmodule

// @latency 1
module dot4_merge(input clk, input rst, input [16:0] left_sum,right_sum, output reg [17:0] dot_result);
    always @(posedge clk) begin // merge_clock
        if(rst) dot_result <= 0;
        else dot_result <= {1'b0,left_sum} + {1'b0,right_sum};
    end
endmodule
