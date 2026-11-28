`timescale 1ns/1ps
// @latency 1
module dot4_pair01 (
    input wire clk,
    input wire rst,
    input wire [7:0] a0,
    input wire [7:0] b0,
    input wire [7:0] a1,
    input wire [7:0] b1,
    output wire [16:0] pair01_sum
);

    (* use_dsp = "yes" *) wire [15:0] product0 = a0 * b0;
    (* use_dsp = "yes" *) wire [15:0] product1 = a1 * b1;
    wire [16:0] sum = {1'b0, product0} + {1'b0, product1};

    reg [16:0] sum_q;

    always @(posedge clk) begin
        if (rst)
            sum_q <= 17'b0;
        else
            sum_q <= sum;
    end

    assign pair01_sum = sum_q;

endmodule

`timescale 1ns/1ps
// @latency 1
module dot4_pair23 (
    input wire clk,
    input wire rst,
    input wire [7:0] a2,
    input wire [7:0] b2,
    input wire [7:0] a3,
    input wire [7:0] b3,
    output wire [16:0] pair23_sum
);

    (* use_dsp = "yes" *) wire [15:0] product2 = a2 * b2;
    (* use_dsp = "yes" *) wire [15:0] product3 = a3 * b3;
    wire [16:0] sum = {1'b0, product2} + {1'b0, product3};

    reg [16:0] pair23_sum_reg;
    assign pair23_sum = pair23_sum_reg;

    always @(posedge clk) begin
        if (rst)
            pair23_sum_reg <= 17'b0;
        else
            pair23_sum_reg <= sum;
    end

endmodule

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
            dot_result_reg <= 18'd0;
        else
            dot_result_reg <= {1'b0, left_sum} + {1'b0, right_sum};
    end

endmodule

`timescale 1ns/1ps
module dot4_pipeline (
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
    output wire [17:0] dot_result
);
    wire [16:0] w_dot4_pair01_pair01_sum;
    wire [16:0] w_dot4_pair23_pair23_sum;

    dot4_pair01 u_dot4_pair01 (
        .clk(clk),
        .rst(rst),
        .a0(a0),
        .b0(b0),
        .a1(a1),
        .b1(b1),
        .pair01_sum(w_dot4_pair01_pair01_sum)
    );

    dot4_pair23 u_dot4_pair23 (
        .clk(clk),
        .rst(rst),
        .a2(a2),
        .b2(b2),
        .a3(a3),
        .b3(b3),
        .pair23_sum(w_dot4_pair23_pair23_sum)
    );

    dot4_merge u_dot4_merge (
        .clk(clk),
        .rst(rst),
        .left_sum(w_dot4_pair01_pair01_sum),
        .right_sum(w_dot4_pair23_pair23_sum),
        .dot_result(dot_result)
    );
endmodule