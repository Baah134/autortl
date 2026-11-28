module rv_decode (
    input wire [31:0] instr,
    output wire [4:0] rs1,
    output wire [4:0] rs2,
    output wire [4:0] rd,
    output wire [31:0] imm,
    output wire [3:0] alu_op,
    output wire [1:0] a_sel,
    output wire b_sel,
    output wire [2:0] kind,
    output wire [2:0] funct3
);
endmodule
