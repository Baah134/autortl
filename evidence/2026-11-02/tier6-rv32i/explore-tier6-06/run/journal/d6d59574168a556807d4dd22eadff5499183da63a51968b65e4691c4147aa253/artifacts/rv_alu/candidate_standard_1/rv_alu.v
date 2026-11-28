`timescale 1ns/1ps
// @latency 0
module rv_alu (
    input  wire [1:0]  a_sel,
    input  wire        b_sel,
    input  wire [3:0]  op,
    input  wire [31:0] rs1_val,
    input  wire [31:0] rs2_val,
    input  wire [31:0] pc_val,
    input  wire [31:0] imm,
    output wire [31:0] y,
    output wire        eq,
    output wire        lt,
    output wire        ltu
);

    wire [31:0] a;
    wire [31:0] b;
    wire signed [31:0] a_signed;
    wire [31:0] arithmetic_right_shift;
    reg  [31:0] y_comb;

    assign a = (a_sel == 2'd0) ? rs1_val :
               (a_sel == 2'd1) ? pc_val  : 32'd0;
    assign b = b_sel ? imm : rs2_val;
    assign a_signed = a;
    assign arithmetic_right_shift = a_signed >>> b[4:0];

    always @(*) begin
        y_comb = 32'd0;
        case (op[2:0])
            3'b000: y_comb = op[3] ? (a - b) : (a + b);
            3'b001: y_comb = a << b[4:0];
            3'b010: y_comb = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            3'b011: y_comb = (a < b) ? 32'd1 : 32'd0;
            3'b100: y_comb = a ^ b;
            3'b101: y_comb = op[3] ? arithmetic_right_shift : (a >> b[4:0]);
            3'b110: y_comb = a | b;
            3'b111: y_comb = a & b;
            default: y_comb = 32'd0;
        endcase
    end

    assign y   = y_comb;
    assign eq  = (rs1_val == rs2_val);
    assign lt  = ($signed(rs1_val) < $signed(rs2_val));
    assign ltu = (rs1_val < rs2_val);

endmodule