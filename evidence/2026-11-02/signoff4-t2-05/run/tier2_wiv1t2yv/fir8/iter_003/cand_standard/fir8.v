`timescale 1ns/1ps
// @latency 1
module fir8 (
    input  wire               clk,
    input  wire               rst,
    input  wire signed [15:0] x_in,
    output reg  signed [31:0] y_out
);
    parameter signed [15:0] C0=16'd3, C1=16'd7, C2=16'd12, C3=16'd18,
                            C4=16'd18, C5=16'd12, C6=16'd7,  C7=16'd3;

    reg signed [15:0] x_d;
    reg [31:0] acc7_sum, acc7_carry;
    reg [31:0] acc6_sum, acc6_carry;
    reg [31:0] acc5_sum, acc5_carry;
    reg [31:0] acc4_sum, acc4_carry;
    reg [31:0] acc3_sum, acc3_carry;
    reg [31:0] acc2_sum, acc2_carry;
    reg [31:0] acc1_sum, acc1_carry;

    wire signed [31:0] p0 = {{16{x_d[15]}}, x_d} * {{16{C0[15]}}, C0};
    wire signed [31:0] p1 = {{16{x_d[15]}}, x_d} * {{16{C1[15]}}, C1};
    wire signed [31:0] p2 = {{16{x_d[15]}}, x_d} * {{16{C2[15]}}, C2};
    wire signed [31:0] p3 = {{16{x_d[15]}}, x_d} * {{16{C3[15]}}, C3};
    wire signed [31:0] p4 = {{16{x_d[15]}}, x_d} * {{16{C4[15]}}, C4};
    wire signed [31:0] p5 = {{16{x_d[15]}}, x_d} * {{16{C5[15]}}, C5};
    wire signed [31:0] p6 = {{16{x_d[15]}}, x_d} * {{16{C6[15]}}, C6};
    wire signed [31:0] p7 = {{16{x_d[15]}}, x_d} * {{16{C7[15]}}, C7};

    wire [31:0] acc6_sum_next =
        p6 ^ acc7_sum ^ acc7_carry;
    wire [31:0] acc6_carry_next =
        ((p6 & acc7_sum) | (p6 & acc7_carry) |
         (acc7_sum & acc7_carry)) << 1;

    wire [31:0] acc5_sum_next =
        p5 ^ acc6_sum ^ acc6_carry;
    wire [31:0] acc5_carry_next =
        ((p5 & acc6_sum) | (p5 & acc6_carry) |
         (acc6_sum & acc6_carry)) << 1;

    wire [31:0] acc4_sum_next =
        p4 ^ acc5_sum ^ acc5_carry;
    wire [31:0] acc4_carry_next =
        ((p4 & acc5_sum) | (p4 & acc5_carry) |
         (acc5_sum & acc5_carry)) << 1;

    wire [31:0] acc3_sum_next =
        p3 ^ acc4_sum ^ acc4_carry;
    wire [31:0] acc3_carry_next =
        ((p3 & acc4_sum) | (p3 & acc4_carry) |
         (acc4_sum & acc4_carry)) << 1;

    wire [31:0] acc2_sum_next =
        p2 ^ acc3_sum ^ acc3_carry;
    wire [31:0] acc2_carry_next =
        ((p2 & acc3_sum) | (p2 & acc3_carry) |
         (acc3_sum & acc3_carry)) << 1;

    wire [31:0] acc1_sum_next =
        p1 ^ acc2_sum ^ acc2_carry;
    wire [31:0] acc1_carry_next =
        ((p1 & acc2_sum) | (p1 & acc2_carry) |
         (acc2_sum & acc2_carry)) << 1;

    always @(posedge clk) begin
        if (rst) begin
            x_d        <= 16'sd0;
            acc7_sum   <= 32'd0;
            acc7_carry <= 32'd0;
            acc6_sum   <= 32'd0;
            acc6_carry <= 32'd0;
            acc5_sum   <= 32'd0;
            acc5_carry <= 32'd0;
            acc4_sum   <= 32'd0;
            acc4_carry <= 32'd0;
            acc3_sum   <= 32'd0;
            acc3_carry <= 32'd0;
            acc2_sum   <= 32'd0;
            acc2_carry <= 32'd0;
            acc1_sum   <= 32'd0;
            acc1_carry <= 32'd0;
            y_out      <= 32'sd0;
        end else begin
            x_d        <= x_in;
            acc7_sum   <= p7;
            acc7_carry <= 32'd0;
            acc6_sum   <= acc6_sum_next;
            acc6_carry <= acc6_carry_next;
            acc5_sum   <= acc5_sum_next;
            acc5_carry <= acc5_carry_next;
            acc4_sum   <= acc4_sum_next;
            acc4_carry <= acc4_carry_next;
            acc3_sum   <= acc3_sum_next;
            acc3_carry <= acc3_carry_next;
            acc2_sum   <= acc2_sum_next;
            acc2_carry <= acc2_carry_next;
            acc1_sum   <= acc1_sum_next;
            acc1_carry <= acc1_carry_next;
            y_out      <= p0 + acc1_sum + acc1_carry;
        end
    end
endmodule