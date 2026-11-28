`timescale 1ns/1ps
// @latency 0
module rv_decode (
    input  wire [31:0] instr,
    output wire [4:0]  rs1,
    output wire [4:0]  rs2,
    output wire [4:0]  rd,
    output reg  [31:0] imm,
    output reg  [3:0]  alu_op,
    output reg  [1:0]  a_sel,
    output reg         b_sel,
    output reg  [2:0]  kind,
    output wire [2:0]  funct3
);

assign rs1    = instr[19:15];
assign rs2    = instr[24:20];
assign rd     = instr[11:7];
assign funct3 = instr[14:12];

always @(*) begin
    imm    = 32'b0;
    alu_op = 4'b0;
    a_sel  = 2'b0;
    b_sel  = 1'b0;
    kind   = 3'd6;

    case (instr[6:0])
        7'b0110011: begin
            kind   = 3'd0;
            alu_op = {instr[30], funct3};
        end

        7'b0010011: begin
            kind   = 3'd0;
            b_sel  = 1'b1;
            imm    = {{20{instr[31]}}, instr[31:20]};
            if (funct3 != 3'b101)
                alu_op = {instr[30], funct3};
            else
                alu_op = {1'b0, funct3};
        end

        7'b0110111: begin
            kind   = 3'd0;
            a_sel  = 2'd2;
            b_sel  = 1'b1;
            imm    = {instr[31:12], 12'b0};
        end

        7'b0010111: begin
            kind   = 3'd0;
            a_sel  = 2'd1;
            b_sel  = 1'b1;
            imm    = {instr[31:12], 12'b0};
        end

        7'b1101111: begin
            kind   = 3'd4;
            a_sel  = 2'd1;
            b_sel  = 1'b1;
            imm    = {{11{instr[31]}}, instr[31], instr[19:12],
                      instr[20], instr[30:21], 1'b0};
        end

        7'b1100111: begin
            kind   = 3'd5;
            b_sel  = 1'b1;
            imm    = {{20{instr[31]}}, instr[31:20]};
        end

        7'b1100011: begin
            kind   = 3'd3;
            a_sel  = 2'd1;
            b_sel  = 1'b1;
            imm    = {{19{instr[31]}}, instr[31], instr[7],
                      instr[30:25], instr[11:8], 1'b0};
        end

        7'b0000011: begin
            kind   = 3'd1;
            b_sel  = 1'b1;
            imm    = {{20{instr[31]}}, instr[31:20]};
        end

        7'b0100011: begin
            kind   = 3'd2;
            b_sel  = 1'b1;
            imm    = {{20{instr[31]}}, instr[31:25], instr[11:7]};
        end

        default: begin
            kind   = 3'd6;
            a_sel  = 2'b0;
            b_sel  = 1'b0;
            alu_op = 4'b0;
            imm    = 32'b0;
        end
    endcase
end

endmodule