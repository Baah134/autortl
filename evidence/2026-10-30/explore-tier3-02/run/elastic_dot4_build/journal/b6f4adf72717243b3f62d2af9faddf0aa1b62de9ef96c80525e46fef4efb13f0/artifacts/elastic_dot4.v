`timescale 1ns/1ps
// @latency 2
module elastic_dot4 (
    input wire clk,
    input wire rst,
    input wire [7:0] a0,
    input wire [7:0] b0,
    input wire [7:0] a1,
    input wire [7:0] b1,
    input wire [7:0] a2,
    input wire [7:0] b2,
    input wire [7:0] a3,
    input wire [7:0] b3,
    input wire in_valid,
    output wire in_ready,
    output wire [17:0] out_data,
    output wire out_valid,
    input wire out_ready
);

    wire [15:0] product0 = a0 * b0;
    wire [15:0] product1 = a1 * b1;
    wire [15:0] product2 = a2 * b2;
    wire [15:0] product3 = a3 * b3;

    wire [16:0] input_sum01 = {1'b0, product0} + {1'b0, product1};
    wire [16:0] input_sum23 = {1'b0, product2} + {1'b0, product3};
    wire [17:0] input_total = {1'b0, input_sum01} + {1'b0, input_sum23};

    reg [17:0] stage1_result;
    reg stage1_valid;

    reg [17:0] stage2_result;
    reg stage2_valid;

    wire stage2_ready = ~stage2_valid | out_ready;

    assign in_ready = ~stage1_valid | stage2_ready;
    assign out_valid = stage2_valid;
    assign out_data = stage2_result;

    always @(posedge clk) begin
        if (rst) begin
            stage1_valid <= 1'b0;
            stage2_valid <= 1'b0;
        end else begin
            if (stage2_ready) begin
                stage2_valid <= stage1_valid;
                if (stage1_valid)
                    stage2_result <= stage1_result;
            end

            if (in_ready) begin
                stage1_valid <= in_valid;
                if (in_valid)
                    stage1_result <= input_total;
            end
        end
    end

endmodule