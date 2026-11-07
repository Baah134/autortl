`timescale 1ns/1ps
// @latency 2
module elastic_dot4_core (
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

    reg [17:0] stage1_result;
    reg valid_stage1;
    reg [17:0] result_stage2;
    reg valid_stage2;

    (* use_dsp = "yes" *) wire [15:0] product_0 = a0 * b0;
    (* use_dsp = "yes" *) wire [15:0] product_1 = a1 * b1;
    (* use_dsp = "yes" *) wire [15:0] product_2 = a2 * b2;
    (* use_dsp = "yes" *) wire [15:0] product_3 = a3 * b3;

    wire [17:0] input_dot =
        {2'b00, product_0} +
        {2'b00, product_1} +
        {2'b00, product_2} +
        {2'b00, product_3};

    wire stage2_ready = !valid_stage2 || out_ready;

    // A direct register output cannot preserve the specified readiness:
    // in_ready must respond combinationally to the current out_ready input.
    assign in_ready = !valid_stage1 || stage2_ready;
    assign out_valid = valid_stage2;
    assign out_data = result_stage2;

    always @(posedge clk) begin
        if (rst) begin
            valid_stage1 <= 1'b0;
            valid_stage2 <= 1'b0;
        end else begin
            if (stage2_ready) begin
                valid_stage2 <= valid_stage1;
                if (valid_stage1)
                    result_stage2 <= stage1_result;
            end

            if (in_ready) begin
                valid_stage1 <= in_valid;
                if (in_valid)
                    stage1_result <= input_dot;
            end
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 2
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
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
    elastic_dot4_core u_elastic_dot4_core (
        .clk(clk),
        .rst(rst),
        .a0(a0),
        .b0(b0),
        .a1(a1),
        .b1(b1),
        .a2(a2),
        .b2(b2),
        .a3(a3),
        .b3(b3),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule