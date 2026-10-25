`timescale 1ns/1ps
// @latency 2
module elastic_dot4_core (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] a0,
    input  wire [7:0] b0,
    input  wire [7:0] a1,
    input  wire [7:0] b1,
    input  wire [7:0] a2,
    input  wire [7:0] b2,
    input  wire [7:0] a3,
    input  wire [7:0] b3,
    input  wire       in_valid,
    output wire       in_ready,
    output wire [17:0] out_data,
    output wire       out_valid,
    input  wire       out_ready
);

    reg        v1;
    reg        v2;
    reg [16:0] p01;
    reg [16:0] p23;
    reg [17:0] result;

    wire [15:0] prod0 = a0 * b0;
    wire [15:0] prod1 = a1 * b1;
    wire [15:0] prod2 = a2 * b2;
    wire [15:0] prod3 = a3 * b3;

    wire [16:0] sum01 = {1'b0, prod0} + {1'b0, prod1};
    wire [16:0] sum23 = {1'b0, prod2} + {1'b0, prod3};
    wire [17:0] total = {1'b0, p01} + {1'b0, p23};

    wire stage2_ready = !v2 || out_ready;

    assign in_ready  = !v1 || stage2_ready;
    assign out_valid = v2;
    assign out_data  = result;

    always @(posedge clk) begin
        if (rst) begin
            v1     <= 1'b0;
            v2     <= 1'b0;
            p01    <= 17'b0;
            p23    <= 17'b0;
            result <= 18'b0;
        end else begin
            if (stage2_ready) begin
                v2 <= v1;
                if (v1)
                    result <= total;
            end

            if (in_ready) begin
                v1 <= in_valid;
                if (in_valid) begin
                    p01 <= sum01;
                    p23 <= sum23;
                end
            end
        end
    end

endmodule