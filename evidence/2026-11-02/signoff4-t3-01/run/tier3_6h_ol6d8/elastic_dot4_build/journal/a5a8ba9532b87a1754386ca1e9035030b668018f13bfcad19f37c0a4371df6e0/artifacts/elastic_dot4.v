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

    reg v1;
    reg v2;
    reg [16:0] partial_lo;
    reg [16:0] partial_hi;
    reg [17:0] result;

    wire stage2_ready;
    assign stage2_ready = !v2 || out_ready;
    assign in_ready = !v1 || stage2_ready;
    assign out_valid = v2;
    assign out_data = result;

    (* use_dsp = "yes" *) wire [15:0] product0 = a0 * b0;
    (* use_dsp = "yes" *) wire [15:0] product1 = a1 * b1;
    (* use_dsp = "yes" *) wire [15:0] product2 = a2 * b2;
    (* use_dsp = "yes" *) wire [15:0] product3 = a3 * b3;

    (* use_dsp = "yes" *) wire [16:0] input_partial_lo = {1'b0, product0} + {1'b0, product1};
    (* use_dsp = "yes" *) wire [16:0] input_partial_hi = {1'b0, product2} + {1'b0, product3};
    wire [17:0] partial_sum = {1'b0, partial_lo} + {1'b0, partial_hi};

    always @(posedge clk) begin
        if (rst) begin
            v1 <= 1'b0;
            v2 <= 1'b0;
        end else begin
            if (stage2_ready) begin
                v2 <= v1;
                if (v1)
                    result <= partial_sum;
            end

            if (in_ready) begin
                v1 <= in_valid;
                if (in_valid) begin
                    partial_lo <= input_partial_lo;
                    partial_hi <= input_partial_hi;
                end
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