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
endmodule
