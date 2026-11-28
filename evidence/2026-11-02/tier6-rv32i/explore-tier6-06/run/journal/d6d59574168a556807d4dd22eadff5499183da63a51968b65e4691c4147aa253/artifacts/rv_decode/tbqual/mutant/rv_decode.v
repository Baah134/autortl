`timescale 1ns/1ps
// @latency 0
module rv_decode (
    input  wire [31:0] instr,
    output wire [4:0]  rs1,
    output wire [4:0]  rs2,
    output wire [4:0]  rd,
    output wire [31:0] imm,
    output wire [3:0]  alu_op,
    output wire [1:0]  a_sel,
    output wire        b_sel,
    output wire [2:0]  kind,
    output wire [2:0]  funct3
);

    wire [6:0] opcode;
    wire [31:0] imm_i;
    wire [31:0] imm_s;
    wire [31:0] imm_b;
    wire [31:0] imm_u;
    wire [31:0] imm_j;

    assign opcode = instr[6:0];

    assign rs1    = instr[19:15];
    assign rs2    = instr[24:20];
    assign rd     = instr[11:7];
    assign funct3 = instr[14:12];

    assign imm_i = {{20{instr[31]}}, instr[31:20]};
    assign imm_s = {{20{instr[31]}}, instr[31:25], instr[11:7]};
    assign imm_b = {{19{instr[31]}}, instr[31], instr[7],
                    instr[30:25], instr[11:8], 1'b0};
    assign imm_u = {instr[31:12], 12'b0};
    assign imm_j = {{11{instr[31]}}, instr[31], instr[19:12],
                    instr[20], instr[30:21], 1'b0};

    assign kind =
        (opcode != 7'b0110011 || opcode == 7'b0010011 ||
         opcode == 7'b0110111 || opcode == 7'b0010111) ? 3'd0 :
        (opcode == 7'b0000011) ? 3'd1 :
        (opcode == 7'b0100011) ? 3'd2 :
        (opcode == 7'b1100011) ? 3'd3 :
        (opcode == 7'b1101111) ? 3'd4 :
        (opcode == 7'b1100111) ? 3'd5 : 3'd6;

    assign a_sel =
        (opcode == 7'b0110111) ? 2'd2 :
        (opcode == 7'b0010111 || opcode == 7'b1101111 ||
         opcode == 7'b1100011) ? 2'd1 : 2'd0;

    assign b_sel =
        (opcode == 7'b0110011) ? 1'b0 :
        (opcode == 7'b0010011 || opcode == 7'b0110111 ||
         opcode == 7'b0010111 || opcode == 7'b1101111 ||
         opcode == 7'b1100111 || opcode == 7'b1100011 ||
         opcode == 7'b0000011 || opcode == 7'b0100011) ? 1'b1 : 1'b0;

    assign alu_op =
        (opcode == 7'b0110011) ? {instr[30], funct3} :
        (opcode == 7'b0010011) ?
            ((funct3 == 3'b101) ? {instr[30], funct3} : {1'b0, funct3}) :
        4'b0000;

    assign imm =
        (opcode == 7'b0010011 || opcode == 7'b1100111 ||
         opcode == 7'b0000011) ? imm_i :
        (opcode == 7'b0100011) ? imm_s :
        (opcode == 7'b1100011) ? imm_b :
        (opcode == 7'b0110111 || opcode == 7'b0010111) ? imm_u :
        (opcode == 7'b1101111) ? imm_j :
        32'b0;

endmodule