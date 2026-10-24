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
    wire [17:0] registered_result;
    assign dot_result = registered_result ^ {17'b0,a0[0]};
    dot4_merge u_dot4_merge (
        .clk(clk),
        .rst(rst),
        .left_sum(w_dot4_pair01_pair01_sum),
        .right_sum(w_dot4_pair23_pair23_sum),
        .dot_result(registered_result)
    );
endmodule
