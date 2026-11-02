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

    reg signed [15:0] d [0:9];

    wire signed [31:0] p0 = d[2] * C0;
    wire signed [31:0] p1 = d[3] * C1;
    wire signed [31:0] p2 = d[4] * C2;
    wire signed [31:0] p3 = d[5] * C3;
    wire signed [31:0] p4 = d[6] * C4;
    wire signed [31:0] p5 = d[7] * C5;
    wire signed [31:0] p6 = d[8] * C6;
    wire signed [31:0] p7 = d[9] * C7;

    wire [31:0] s1a = p0 ^ p1 ^ p2;
    wire [31:0] c1a = ((p0 & p1) | (p0 & p2) | (p1 & p2)) << 1;
    wire [31:0] s1b = p3 ^ p4 ^ p5;
    wire [31:0] c1b = ((p3 & p4) | (p3 & p5) | (p4 & p5)) << 1;

    wire [31:0] s2a = s1a ^ c1a ^ s1b;
    wire [31:0] c2a = ((s1a & c1a) | (s1a & s1b) | (c1a & s1b)) << 1;
    wire [31:0] s2b = c1b ^ p6 ^ p7;
    wire [31:0] c2b = ((c1b & p6) | (c1b & p7) | (p6 & p7)) << 1;

    wire [31:0] s3a = s2a ^ c2a ^ s2b;
    wire [31:0] c3a = ((s2a & c2a) | (s2a & s2b) | (c2a & s2b)) << 1;

    wire [31:0] s4a = s3a ^ c3a ^ c2b;
    wire [31:0] c4a = ((s3a & c3a) | (s3a & c2b) | (c3a & c2b)) << 1;

    wire [31:0] add_a = s4a;
    wire [31:0] add_b = c4a;

    wire [8:0] add0 = {1'b0, add_a[7:0]} + {1'b0, add_b[7:0]};
    wire [8:0] add1 = {1'b0, add_a[15:8]} + {1'b0, add_b[15:8]};
    wire [8:0] add2 = {1'b0, add_a[23:16]} + {1'b0, add_b[23:16]};
    wire [8:0] add3 = {1'b0, add_a[31:24]} + {1'b0, add_b[31:24]};

    wire prop0 = &(add_a[7:0] ^ add_b[7:0]);
    wire prop1 = &(add_a[15:8] ^ add_b[15:8]);
    wire prop2 = &(add_a[23:16] ^ add_b[23:16]);

    wire carry0 = 1'b0;
    wire carry1 = add0[8];
    wire carry2 = add1[8] | (prop1 & carry1);
    wire carry3 = add2[8] | (prop2 & add1[8]) | (prop2 & prop1 & carry1);

    wire [31:0] sum = {
        (add_a[31:24] + add_b[31:24] + carry3),
        (add_a[23:16] + add_b[23:16] + carry2),
        (add_a[15:8]  + add_b[15:8]  + carry1),
        (add_a[7:0]   + add_b[7:0]   + carry0)
    };

    integer i;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 10; i = i + 1)
                d[i] <= 16'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 10; i = i + 1)
                d[i] <= d[i-1];
            y_out <= sum;
        end
    end
endmodule