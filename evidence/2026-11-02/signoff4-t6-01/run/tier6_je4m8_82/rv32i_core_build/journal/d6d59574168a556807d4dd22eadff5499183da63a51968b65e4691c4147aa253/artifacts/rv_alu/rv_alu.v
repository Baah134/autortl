`timescale 1ns/1ps
// @latency 0
module rv_alu (
    input wire [1:0] a_sel,
    input wire b_sel,
    input wire [3:0] op,
    input wire [31:0] rs1_val,
    input wire [31:0] rs2_val,
    input wire [31:0] pc_val,
    input wire [31:0] imm,
    output wire [31:0] y,
    output wire eq,
    output wire lt,
    output wire ltu
);

    reg [31:0] a;
    reg [31:0] b;
    reg [31:0] y_comb;

    always @(*) begin
        a = 32'b0;
        case (a_sel)
            2'b00: a = rs1_val;
            2'b01: a = pc_val;
            default: a = 32'b0;
        endcase

        b = rs2_val;
        if (b_sel)
            b = imm;

        y_comb = 32'b0;
        case (op[2:0])
            3'b000: begin
                if (op[3])
                    y_comb = a - b;
                else
                    y_comb = a + b;
            end
            3'b001: y_comb = a << b[4:0];
            3'b010: y_comb = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            3'b011: y_comb = (a < b) ? 32'd1 : 32'd0;
            3'b100: y_comb = a ^ b;
            3'b101: begin
                if (op[3])
                    y_comb = $signed(a) >>> b[4:0];
                else
                    y_comb = a >> b[4:0];
            end
            3'b110: y_comb = a | b;
            3'b111: y_comb = a & b;
        endcase
    end

    assign y = y_comb;
    assign eq = (rs1_val == rs2_val);
    assign lt = ($signed(rs1_val) < $signed(rs2_val));
    assign ltu = (rs1_val < rs2_val);

endmodule