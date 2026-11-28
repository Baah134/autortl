`timescale 1ns/1ps
module rv32i_core (
    input wire clk,
    input wire rst,
    input wire run,
    input wire imem_we,
    input wire [5:0] imem_waddr,
    input wire [31:0] imem_wdata,
    output wire [31:0] pc,
    output wire retire,
    output wire rf_we,
    output wire [4:0] rf_waddr,
    output wire [31:0] rf_wdata,
    output wire dmem_we,
    output wire [4:0] dmem_addr,
    output wire [31:0] dmem_wdata
);
    wire [5:0] w_rv_ctrl_imem_raddr;
    wire [31:0] w_rv_imem_imem_rdata;
    wire [4:0] w_rv_decode_rs1;
    wire [4:0] w_rv_decode_rs2;
    wire [31:0] w_rv_regfile_rdata1;
    wire [31:0] w_rv_regfile_rdata2;
    wire [31:0] w_rv_ctrl_pc;
    wire [31:0] w_rv_decode_imm;
    wire [3:0] w_rv_decode_alu_op;
    wire [1:0] w_rv_decode_a_sel;
    wire w_rv_decode_b_sel;
    wire [2:0] w_rv_decode_kind;
    wire [2:0] w_rv_decode_funct3;
    wire [4:0] w_rv_decode_rd;
    wire [31:0] w_rv_alu_y;
    wire w_rv_alu_eq;
    wire w_rv_alu_lt;
    wire w_rv_alu_ltu;
    wire w_rv_ctrl_rf_we;
    wire [4:0] w_rv_ctrl_rf_waddr;
    wire [31:0] w_rv_ctrl_rf_wdata;
    wire w_rv_ctrl_dmem_we;
    wire [4:0] w_rv_ctrl_dmem_addr;
    wire [31:0] w_rv_ctrl_dmem_wdata;
    wire [31:0] w_rv_dmem_rdata;
    rv_imem u_rv_imem (
        .clk(clk),
        .rst(rst),
        .imem_we(imem_we),
        .imem_waddr(imem_waddr),
        .imem_wdata(imem_wdata),
        .imem_raddr(w_rv_ctrl_imem_raddr),
        .imem_rdata(w_rv_imem_imem_rdata)
    );
    rv_decode u_rv_decode (
        .instr(w_rv_imem_imem_rdata),
        .rs1(w_rv_decode_rs1),
        .rs2(w_rv_decode_rs2),
        .rd(w_rv_decode_rd),
        .imm(w_rv_decode_imm),
        .alu_op(w_rv_decode_alu_op),
        .a_sel(w_rv_decode_a_sel),
        .b_sel(w_rv_decode_b_sel),
        .kind(w_rv_decode_kind),
        .funct3(w_rv_decode_funct3)
    );
    rv_regfile u_rv_regfile (
        .clk(clk),
        .rst(rst),
        .we(w_rv_ctrl_rf_we),
        .waddr(w_rv_ctrl_rf_waddr),
        .wdata(w_rv_ctrl_rf_wdata),
        .raddr1(w_rv_decode_rs1),
        .raddr2(w_rv_decode_rs2),
        .rdata1(w_rv_regfile_rdata1),
        .rdata2(w_rv_regfile_rdata2)
    );
    rv_alu u_rv_alu (
        .a_sel(w_rv_decode_a_sel),
        .b_sel(w_rv_decode_b_sel),
        .op(w_rv_decode_alu_op),
        .rs1_val(w_rv_regfile_rdata1),
        .rs2_val(w_rv_regfile_rdata2),
        .pc_val(w_rv_ctrl_pc),
        .imm(w_rv_decode_imm),
        .y(w_rv_alu_y),
        .eq(w_rv_alu_eq),
        .lt(w_rv_alu_lt),
        .ltu(w_rv_alu_ltu)
    );
    rv_dmem u_rv_dmem (
        .clk(clk),
        .rst(rst),
        .we(w_rv_ctrl_dmem_we),
        .addr(w_rv_ctrl_dmem_addr),
        .wdata(w_rv_ctrl_dmem_wdata),
        .rdata(w_rv_dmem_rdata)
    );
    assign pc = w_rv_ctrl_pc;
    assign rf_we = w_rv_ctrl_rf_we;
    assign rf_waddr = w_rv_ctrl_rf_waddr;
    assign rf_wdata = w_rv_ctrl_rf_wdata;
    assign dmem_we = w_rv_ctrl_dmem_we;
    assign dmem_addr = w_rv_ctrl_dmem_addr;
    assign dmem_wdata = w_rv_ctrl_dmem_wdata;
    rv_ctrl u_rv_ctrl (
        .clk(clk),
        .rst(rst),
        .run(run),
        .kind(w_rv_decode_kind),
        .funct3(w_rv_decode_funct3),
        .rd(w_rv_decode_rd),
        .y(w_rv_alu_y),
        .eq(w_rv_alu_eq),
        .lt(w_rv_alu_lt),
        .ltu(w_rv_alu_ltu),
        .rs2_val(w_rv_regfile_rdata2),
        .dmem_rdata(w_rv_dmem_rdata),
        .pc(w_rv_ctrl_pc),
        .imem_raddr(w_rv_ctrl_imem_raddr),
        .retire(retire),
        .rf_we(w_rv_ctrl_rf_we),
        .rf_waddr(w_rv_ctrl_rf_waddr),
        .rf_wdata(w_rv_ctrl_rf_wdata),
        .dmem_we(w_rv_ctrl_dmem_we),
        .dmem_addr(w_rv_ctrl_dmem_addr),
        .dmem_wdata(w_rv_ctrl_dmem_wdata)
    );
endmodule
