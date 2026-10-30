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

    reg signed [31:0] p_delay [0:7];
    reg signed [31:0] sum_pipe0_a;
    reg signed [31:0] sum_pipe0_b;
    reg signed [31:0] sum_pipe1;
    integer i;

    wire signed [31:0] x_ext = {{16{x_in[15]}}, x_in};
    wire signed [31:0] c0_ext = {{16{C0[15]}}, C0};
    wire signed [31:0] c1_ext = {{16{C1[15]}}, C1};
    wire signed [31:0] c2_ext = {{16{C2[15]}}, C2};
    wire signed [31:0] c3_ext = {{16{C3[15]}}, C3};
    wire signed [31:0] c4_ext = {{16{C4[15]}}, C4};
    wire signed [31:0] c5_ext = {{16{C5[15]}}, C5};
    wire signed [31:0] c6_ext = {{16{C6[15]}}, C6};
    wire signed [31:0] c7_ext = {{16{C7[15]}}, C7};

    wire signed [31:0] p0 = p_delay[0];
    wire signed [31:0] p1 = p_delay[1];
    wire signed [31:0] p2 = p_delay[2];
    wire signed [31:0] p3 = p_delay[3];
    wire signed [31:0] p4 = p_delay[4];
    wire signed [31:0] p5 = p_delay[5];
    wire signed [31:0] p6 = p_delay[6];
    wire signed [31:0] p7 = p_delay[7];

    wire signed [31:0] sum_a = (p0 + p1) + (p2 + p3);
    wire signed [31:0] sum_b = (p4 + p5) + (p6 + p7);

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                p_delay[i] <= 32'sd0;
            sum_pipe0_a <= 32'sd0;
            sum_pipe0_b <= 32'sd0;
            sum_pipe1 <= 32'sd0;
            y_out <= 32'sd0;
        end else begin
            p_delay[0] <= x_ext * c0_ext;
            p_delay[1] <= x_ext * c1_ext;
            p_delay[2] <= x_ext * c2_ext;
            p_delay[3] <= x_ext * c3_ext;
            p_delay[4] <= x_ext * c4_ext;
            p_delay[5] <= x_ext * c5_ext;
            p_delay[6] <= x_ext * c6_ext;
            p_delay[7] <= x_ext * c7_ext;
            for (i = 1; i < 8; i = i + 1)
                p_delay[i] <= p_delay[i-1];

            sum_pipe0_a <= sum_a;
            sum_pipe0_b <= sum_b;
            sum_pipe1 <= sum_pipe0_a + sum_pipe0_b;
            y_out <= sum_pipe1;
        end
    end
endmodule