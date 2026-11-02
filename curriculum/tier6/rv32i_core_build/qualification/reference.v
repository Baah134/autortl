`timescale 1ns/1ps
// Qualification reference only: rv32i_core_tb.v must pass this source and
// fail every mutant in mutants.json. Never configured as a generation seed.
// The top below is byte-identical to the harness's mechanical wrapper.
// @latency 1
// Cycle-level: 64-word instruction memory, read-first registered read port.
module rv_imem (
    input wire clk,
    input wire rst,
    input wire imem_we,
    input wire [5:0] imem_waddr,
    input wire [31:0] imem_wdata,
    input wire [5:0] imem_raddr,
    output reg [31:0] imem_rdata
);
    reg [31:0] mem [0:63];
    integer n;

    always @(posedge clk) begin // imem_clock
        if (rst) begin
            for (n = 0; n < 64; n = n + 1) mem[n] <= 32'd0;
            imem_rdata <= 32'd0;
        end else begin
            imem_rdata <= mem[imem_raddr];
            if (imem_we) mem[imem_waddr] <= imem_wdata;
        end
    end
endmodule

// @latency 0
// Combinational RV32I decoder: register fields, immediate, ALU controls, kind.
module rv_decode (
    input wire [31:0] instr,
    output wire [4:0] rs1,
    output wire [4:0] rs2,
    output wire [4:0] rd,
    output reg [31:0] imm,
    output reg [3:0] alu_op,
    output reg [1:0] a_sel,
    output reg b_sel,
    output reg [2:0] kind,
    output wire [2:0] funct3
);
    wire [6:0] opcode = instr[6:0];
    wire [31:0] imm_i = {{20{instr[31]}}, instr[31:20]};
    wire [31:0] imm_s = {{20{instr[31]}}, instr[31:25], instr[11:7]};
    wire [31:0] imm_b = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
    wire [31:0] imm_u = {instr[31:12], 12'd0};
    wire [31:0] imm_j = {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};
    assign rs1 = instr[19:15];
    assign rs2 = instr[24:20];
    assign rd = instr[11:7];
    assign funct3 = instr[14:12];

    always @(*) begin
        kind = 3'd6;
        a_sel = 2'd0;
        b_sel = 1'b0;
        alu_op = 4'd0;
        imm = 32'd0;
        case (opcode)
            7'b0110011: begin kind = 3'd0; alu_op = {instr[30], funct3}; end
            7'b0010011: begin
                kind = 3'd0; b_sel = 1'b1; imm = imm_i;
                alu_op = {(funct3 == 3'b101) ? instr[30] : 1'b0, funct3};
            end
            7'b0110111: begin kind = 3'd0; a_sel = 2'd2; b_sel = 1'b1; imm = imm_u; end
            7'b0010111: begin kind = 3'd0; a_sel = 2'd1; b_sel = 1'b1; imm = imm_u; end
            7'b1101111: begin kind = 3'd4; a_sel = 2'd1; b_sel = 1'b1; imm = imm_j; end
            7'b1100111: begin kind = 3'd5; b_sel = 1'b1; imm = imm_i; end
            7'b1100011: begin kind = 3'd3; a_sel = 2'd1; b_sel = 1'b1; imm = imm_b; end
            7'b0000011: begin kind = 3'd1; b_sel = 1'b1; imm = imm_i; end
            7'b0100011: begin kind = 3'd2; b_sel = 1'b1; imm = imm_s; end
            default: kind = 3'd6;
        endcase
    end
endmodule

// @latency 1
// Cycle-level: 32 x 32 register file, x0 reads zero, registered read-first ports.
module rv_regfile (
    input wire clk,
    input wire rst,
    input wire we,
    input wire [4:0] waddr,
    input wire [31:0] wdata,
    input wire [4:0] raddr1,
    input wire [4:0] raddr2,
    output reg [31:0] rdata1,
    output reg [31:0] rdata2
);
    reg [31:0] regs [0:31];
    integer n;

    always @(posedge clk) begin // regfile_clock
        if (rst) begin
            for (n = 0; n < 32; n = n + 1) regs[n] <= 32'd0;
            rdata1 <= 32'd0;
            rdata2 <= 32'd0;
        end else begin
            rdata1 <= regs[raddr1];
            rdata2 <= regs[raddr2];
            if (we && waddr != 5'd0) regs[waddr] <= wdata;
        end
    end
endmodule

// @latency 0
// Combinational ALU with operand selection and raw rs1/rs2 comparison flags.
module rv_alu (
    input wire [1:0] a_sel,
    input wire b_sel,
    input wire [3:0] op,
    input wire [31:0] rs1_val,
    input wire [31:0] rs2_val,
    input wire [31:0] pc_val,
    input wire [31:0] imm,
    output reg [31:0] y,
    output wire eq,
    output wire lt,
    output wire ltu
);
    wire [31:0] a = (a_sel == 2'd0) ? rs1_val : (a_sel == 2'd1) ? pc_val : 32'd0;
    wire [31:0] b = b_sel ? imm : rs2_val;
    wire [4:0] sh = b[4:0];
    assign eq = rs1_val == rs2_val;
    assign lt = $signed(rs1_val) < $signed(rs2_val);
    assign ltu = rs1_val < rs2_val;

    always @(*) begin
        case (op[2:0])
            3'b000: y = op[3] ? a - b : a + b;
            3'b001: y = a << sh;
            3'b010: y = {31'd0, $signed(a) < $signed(b)};
            3'b011: y = {31'd0, a < b};
            3'b100: y = a ^ b;
            3'b101: y = op[3] ? $unsigned($signed(a) >>> sh) : a >> sh;
            3'b110: y = a | b;
            default: y = a & b;
        endcase
    end
endmodule

// @latency 1
// Cycle-level: 32-word data memory, one address, read-first registered read.
module rv_dmem (
    input wire clk,
    input wire rst,
    input wire we,
    input wire [4:0] addr,
    input wire [31:0] wdata,
    output reg [31:0] rdata
);
    reg [31:0] mem [0:31];
    integer n;

    always @(posedge clk) begin // dmem_clock
        if (rst) begin
            for (n = 0; n < 32; n = n + 1) mem[n] <= 32'd0;
            rdata <= 32'd0;
        end else begin
            rdata <= mem[addr];
            if (we) mem[addr] <= wdata;
        end
    end
endmodule

// @latency 1
// Cycle-level multi-cycle sequencer: F, D, E, M, L, W; every output is a view of registered state.
module rv_ctrl (
    input wire clk,
    input wire rst,
    input wire run,
    input wire [2:0] kind,
    input wire [2:0] funct3,
    input wire [4:0] rd,
    input wire [31:0] y,
    input wire eq,
    input wire lt,
    input wire ltu,
    input wire [31:0] rs2_val,
    input wire [31:0] dmem_rdata,
    output reg [31:0] pc,
    output wire [5:0] imem_raddr,
    output wire retire,
    output wire rf_we,
    output wire [4:0] rf_waddr,
    output wire [31:0] rf_wdata,
    output wire dmem_we,
    output wire [4:0] dmem_addr,
    output wire [31:0] dmem_wdata
);
    localparam [2:0] S_F = 3'd0, S_D = 3'd1, S_E = 3'd2, S_M = 3'd3, S_L = 3'd4, S_W = 3'd5;
    reg [2:0] state;
    reg [31:0] npc, res, sdata;
    reg [4:0] rd_q;
    reg wb_q, st_q, ld_q;

    wire [31:0] link = pc + 32'd4;
    reg taken;
    always @(*) begin
        case (funct3)
            3'b000: taken = eq;
            3'b001: taken = !eq;
            3'b100: taken = lt;
            3'b101: taken = !lt;
            3'b110: taken = ltu;
            3'b111: taken = !ltu;
            default: taken = 1'b0;
        endcase
    end

    assign imem_raddr = pc[7:2];
    assign retire = state == S_W;
    assign rf_we = retire && wb_q;
    assign rf_waddr = rd_q;
    assign rf_wdata = res;
    assign dmem_we = (state == S_M) && st_q;
    assign dmem_addr = res[6:2];
    assign dmem_wdata = sdata;

    always @(posedge clk) begin // ctrl_clock
        if (rst) begin
            state <= S_F;
            pc <= 32'd0;
            npc <= 32'd0;
            res <= 32'd0;
            sdata <= 32'd0;
            rd_q <= 5'd0;
            wb_q <= 1'b0;
            st_q <= 1'b0;
            ld_q <= 1'b0;
        end else begin
            case (state)
                S_F: if (run) state <= S_D;
                S_D: state <= S_E;
                S_E: begin
                    wb_q <= (kind == 3'd0) || (kind == 3'd1) || (kind == 3'd4) || (kind == 3'd5);
                    st_q <= kind == 3'd2;
                    ld_q <= kind == 3'd1;
                    rd_q <= rd;
                    sdata <= rs2_val;
                    res <= (kind == 3'd4 || kind == 3'd5) ? link : y;
                    if (kind == 3'd4 || (kind == 3'd3 && taken)) npc <= y;
                    else if (kind == 3'd5) npc <= {y[31:1], 1'b0};
                    else npc <= link;
                    state <= (kind == 3'd1 || kind == 3'd2) ? S_M : S_W;
                end
                S_M: state <= ld_q ? S_L : S_W;
                S_L: begin res <= dmem_rdata; state <= S_W; end
                S_W: begin pc <= npc; state <= S_F; end
                default: state <= S_F;
            endcase
        end
    end
endmodule

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
