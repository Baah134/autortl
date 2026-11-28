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

    reg [31:0] imm_r;
    reg [3:0]  alu_op_r;
    reg [1:0]  a_sel_r;
    reg        b_sel_r;
    reg [2:0]  kind_r;

    assign rs1    = instr[19:15];
    assign rs2    = instr[24:20];
    assign rd     = instr[11:7];
    assign funct3 = instr[14:12];

    assign imm    = imm_r;
    assign alu_op = alu_op_r;
    assign a_sel  = a_sel_r;
    assign b_sel  = b_sel_r;
    assign kind   = kind_r;

    always @(*) begin
        imm_r    = 32'b0;
        alu_op_r = 4'b0;
        a_sel_r  = 2'b0;
        b_sel_r  = 1'b0;
        kind_r   = 3'd6;

        case (instr[6:0])
            7'b0110011: begin
                kind_r   = 3'd0;
                alu_op_r = {instr[30], instr[14:12]};
            end
            7'b0010011: begin
                kind_r   = 3'd0;
                b_sel_r  = 1'b1;
                imm_r    = {{20{instr[31]}}, instr[31:20]};
                if (instr[14:12] != 3'b101)
                    alu_op_r = {instr[30], instr[14:12]};
                else
                    alu_op_r = {1'b0, instr[14:12]};
            end
            7'b0110111: begin
                kind_r   = 3'd0;
                a_sel_r  = 2'd2;
                b_sel_r  = 1'b1;
                imm_r    = {instr[31:12], 12'b0};
            end
            7'b0010111: begin
                kind_r   = 3'd0;
                a_sel_r  = 2'd1;
                b_sel_r  = 1'b1;
                imm_r    = {instr[31:12], 12'b0};
            end
            7'b1101111: begin
                kind_r   = 3'd4;
                a_sel_r  = 2'd1;
                b_sel_r  = 1'b1;
                imm_r    = {{11{instr[31]}}, instr[31], instr[19:12],
                            instr[20], instr[30:21], 1'b0};
            end
            7'b1100111: begin
                kind_r   = 3'd5;
                b_sel_r  = 1'b1;
                imm_r    = {{20{instr[31]}}, instr[31:20]};
            end
            7'b1100011: begin
                kind_r   = 3'd3;
                a_sel_r  = 2'd1;
                b_sel_r  = 1'b1;
                imm_r    = {{19{instr[31]}}, instr[31], instr[7],
                            instr[30:25], instr[11:8], 1'b0};
            end
            7'b0000011: begin
                kind_r   = 3'd1;
                b_sel_r  = 1'b1;
                imm_r    = {{20{instr[31]}}, instr[31:20]};
            end
            7'b0100011: begin
                kind_r   = 3'd2;
                b_sel_r  = 1'b1;
                imm_r    = {{20{instr[31]}}, instr[31:25], instr[11:7]};
            end
            default: begin
                kind_r = 3'd6;
            end
        endcase
    end

endmodule