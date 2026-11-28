`timescale 1ns/1ps
// @latency 1
module rv_imem (
    input wire clk,
    input wire rst,
    input wire imem_we,
    input wire [5:0] imem_waddr,
    input wire [31:0] imem_wdata,
    input wire [5:0] imem_raddr,
    output wire [31:0] imem_rdata
);
    reg [31:0] mem [0:63];
    reg [31:0] imem_rdata_reg;
    integer i;

    assign imem_rdata = imem_rdata_reg;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 64; i = i + 1)
                mem[i] <= 32'b0;
            imem_rdata_reg <= 32'b0;
        end else begin
            imem_rdata_reg <= mem[imem_raddr];
            if (imem_we)
                mem[imem_waddr] <= imem_wdata;
        end
    end
endmodule

`timescale 1ns/1ps
// @latency 0
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
    reg [31:0] imm_r;
    reg [3:0] alu_op_r;
    reg [1:0] a_sel_r;
    reg b_sel_r;
    reg [2:0] kind_r;

    assign rs1 = instr[19:15];
    assign rs2 = instr[24:20];
    assign rd = instr[11:7];
    assign funct3 = instr[14:12];
    assign imm = imm_r;
    assign alu_op = alu_op_r;
    assign a_sel = a_sel_r;
    assign b_sel = b_sel_r;
    assign kind = kind_r;

    always @(*) begin
        imm_r = 32'b0;
        alu_op_r = 4'b0;
        a_sel_r = 2'b0;
        b_sel_r = 1'b0;
        kind_r = 3'd6;

        case (instr[6:0])
            7'b0110011: begin
                kind_r = 3'd0;
                alu_op_r = {instr[30], instr[14:12]};
            end
            7'b0010011: begin
                kind_r = 3'd0;
                b_sel_r = 1'b1;
                imm_r = {{20{instr[31]}}, instr[31:20]};
                if (instr[14:12] == 3'b101)
                    alu_op_r = {instr[30], instr[14:12]};
                else
                    alu_op_r = {1'b0, instr[14:12]};
            end
            7'b0110111: begin
                kind_r = 3'd0;
                a_sel_r = 2'd2;
                b_sel_r = 1'b1;
                imm_r = {instr[31:12], 12'b0};
            end
            7'b0010111: begin
                kind_r = 3'd0;
                a_sel_r = 2'd1;
                b_sel_r = 1'b1;
                imm_r = {instr[31:12], 12'b0};
            end
            7'b1101111: begin
                kind_r = 3'd4;
                a_sel_r = 2'd1;
                b_sel_r = 1'b1;
                imm_r = {{11{instr[31]}}, instr[31], instr[19:12],
                         instr[20], instr[30:21], 1'b0};
            end
            7'b1100111: begin
                kind_r = 3'd5;
                b_sel_r = 1'b1;
                imm_r = {{20{instr[31]}}, instr[31:20]};
            end
            7'b1100011: begin
                kind_r = 3'd3;
                a_sel_r = 2'd1;
                b_sel_r = 1'b1;
                imm_r = {{19{instr[31]}}, instr[31], instr[7],
                         instr[30:25], instr[11:8], 1'b0};
            end
            7'b0000011: begin
                kind_r = 3'd1;
                b_sel_r = 1'b1;
                imm_r = {{20{instr[31]}}, instr[31:20]};
            end
            7'b0100011: begin
                kind_r = 3'd2;
                b_sel_r = 1'b1;
                imm_r = {{20{instr[31]}}, instr[31:25], instr[11:7]};
            end
            default: begin
                kind_r = 3'd6;
            end
        endcase
    end
endmodule

`timescale 1ns/1ps
// @latency 1
module rv_regfile (
    input wire clk,
    input wire rst,
    input wire we,
    input wire [4:0] waddr,
    input wire [31:0] wdata,
    input wire [4:0] raddr1,
    input wire [4:0] raddr2,
    output wire [31:0] rdata1,
    output wire [31:0] rdata2
);
    reg [31:0] regs [1:31];
    reg [31:0] rdata1_reg;
    reg [31:0] rdata2_reg;
    integer i;

    assign rdata1 = rdata1_reg;
    assign rdata2 = rdata2_reg;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 1; i < 32; i = i + 1)
                regs[i] <= 32'b0;
            rdata1_reg <= 32'b0;
            rdata2_reg <= 32'b0;
        end else begin
            if (raddr1 == 5'b0)
                rdata1_reg <= 32'b0;
            else
                rdata1_reg <= regs[raddr1];

            if (raddr2 == 5'b0)
                rdata2_reg <= 32'b0;
            else
                rdata2_reg <= regs[raddr2];

            if (we && (waddr != 5'b0))
                regs[waddr] <= wdata;
        end
    end
endmodule

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
    reg [31:0] y_comb;
    wire [31:0] a;
    wire [31:0] b;
    wire subtract;
    wire [31:0] b_addsub;
    wire [32:0] add_sub_extended;
    wire [31:0] add_sub_result;
    wire signed_overflow;
    wire signed_less;
    wire unsigned_less;
    wire [31:0] a_reversed;
    wire [31:0] shift_input;
    wire [32:0] shift_extended;
    wire [32:0] shift_right_extended;
    wire [31:0] shift_right_result;
    wire [31:0] shift_result;
    wire shift_left;
    wire shift_arithmetic;
    genvar i;

    assign a = (a_sel == 2'd0) ? rs1_val :
               (a_sel == 2'd1) ? pc_val : 32'd0;
    assign b = b_sel ? imm : rs2_val;
    assign subtract = op[3] || (op[2:0] == 3'b010) ||
                      (op[2:0] == 3'b011);
    assign b_addsub = b ^ {32{subtract}};
    assign add_sub_extended = {1'b0, a} + {1'b0, b_addsub} + subtract;
    assign add_sub_result = add_sub_extended[31:0];
    assign signed_overflow = (a[31] ^ b[31]) &
                             (a[31] ^ add_sub_result[31]);
    assign signed_less = add_sub_result[31] ^ signed_overflow;
    assign unsigned_less = ~add_sub_extended[32];

    generate
        for (i = 0; i < 32; i = i + 1) begin : reverse_bits
            assign a_reversed[i] = a[31-i];
        end
    endgenerate

    assign shift_left = (op[2:0] == 3'b001);
    assign shift_arithmetic = (op[2:0] == 3'b101) && op[3];
    assign shift_input = shift_left ? a_reversed : a;
    assign shift_extended = {shift_arithmetic && shift_input[31], shift_input};
    assign shift_right_extended = $signed(shift_extended) >>> b[4:0];

    generate
        for (i = 0; i < 32; i = i + 1) begin : reverse_shift_result
            assign shift_right_result[i] = shift_right_extended[i];
            assign shift_result[i] = shift_left ?
                                     shift_right_result[31-i] :
                                     shift_right_result[i];
        end
    endgenerate

    assign y = y_comb;
    assign eq = (rs1_val == rs2_val);
    assign lt = ($signed(rs1_val) < $signed(rs2_val));
    assign ltu = (rs1_val < rs2_val);

    always @(*) begin
        y_comb = 32'd0;
        case (op[2:0])
            3'b000: y_comb = add_sub_result;
            3'b001: y_comb = shift_result;
            3'b010: y_comb = signed_less ? 32'd1 : 32'd0;
            3'b011: y_comb = unsigned_less ? 32'd1 : 32'd0;
            3'b100: y_comb = a ^ b;
            3'b101: y_comb = shift_result;
            3'b110: y_comb = a | b;
            3'b111: y_comb = a & b;
            default: y_comb = 32'd0;
        endcase
    end
endmodule

`timescale 1ns/1ps
// @latency 1
module rv_dmem (
    input wire clk,
    input wire rst,
    input wire we,
    input wire [4:0] addr,
    input wire [31:0] wdata,
    output wire [31:0] rdata
);
    reg [31:0] mem [0:31];
    reg [31:0] rdata_reg;
    integer i;

    assign rdata = rdata_reg;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 32; i = i + 1)
                mem[i] <= 32'b0;
            rdata_reg <= 32'b0;
        end else begin
            rdata_reg <= mem[addr];
            if (we)
                mem[addr] <= wdata;
        end
    end
endmodule

`timescale 1ns/1ps
// @latency 1
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
    output wire [31:0] pc,
    output wire [5:0] imem_raddr,
    output wire retire,
    output wire rf_we,
    output wire [4:0] rf_waddr,
    output wire [31:0] rf_wdata,
    output wire dmem_we,
    output wire [4:0] dmem_addr,
    output wire [31:0] dmem_wdata
);
    localparam [2:0] F = 3'd0;
    localparam [2:0] D = 3'd1;
    localparam [2:0] E = 3'd2;
    localparam [2:0] M = 3'd3;
    localparam [2:0] L = 3'd4;
    localparam [2:0] W = 3'd5;

    reg [2:0] state;
    reg [31:0] pc_q;
    reg [31:0] npc;
    reg [31:0] res;
    reg [31:0] sdata;
    reg [4:0] rd_q;
    reg wb_q;
    reg st_q;
    reg ld_q;

    wire taken;
    wire [31:0] link;

    assign taken =
        (funct3 == 3'b000) ? eq :
        (funct3 == 3'b001) ? !eq :
        (funct3 == 3'b100) ? lt :
        (funct3 == 3'b101) ? !lt :
        (funct3 == 3'b110) ? ltu :
        (funct3 == 3'b111) ? !ltu : 1'b0;

    assign link = pc_q + 32'd4;

    assign pc = pc_q;
    assign imem_raddr = pc_q[7:2];
    assign retire = (state == W);
    assign rf_we = (state == W) && wb_q;
    assign rf_waddr = rd_q;
    assign rf_wdata = res;
    assign dmem_we = (state == M) && st_q;
    assign dmem_addr = res[6:2];
    assign dmem_wdata = sdata;

    always @(posedge clk) begin
        if (rst) begin
            state <= F;
            pc_q <= 32'b0;
            npc <= 32'b0;
            res <= 32'b0;
            sdata <= 32'b0;
            rd_q <= 5'b0;
            wb_q <= 1'b0;
            st_q <= 1'b0;
            ld_q <= 1'b0;
        end else begin
            case (state)
                F: begin
                    if (run)
                        state <= D;
                end
                D: begin
                    state <= E;
                end
                E: begin
                    wb_q <= (kind == 3'd0) || (kind == 3'd1) ||
                            (kind == 3'd4) || (kind == 3'd5);
                    st_q <= (kind == 3'd2);
                    ld_q <= (kind == 3'd1);
                    rd_q <= rd;
                    sdata <= rs2_val;

                    if ((kind == 3'd4) || (kind == 3'd5))
                        res <= link;
                    else
                        res <= y;

                    if ((kind == 3'd4) || ((kind == 3'd3) && taken))
                        npc <= y;
                    else if (kind == 3'd5)
                        npc <= {y[31:1], 1'b0};
                    else
                        npc <= link;

                    if ((kind == 3'd1) || (kind == 3'd2))
                        state <= M;
                    else
                        state <= W;
                end
                M: begin
                    if (ld_q)
                        state <= L;
                    else
                        state <= W;
                end
                L: begin
                    res <= dmem_rdata;
                    state <= W;
                end
                W: begin
                    pc_q <= npc;
                    state <= F;
                end
                default: begin
                    state <= F;
                end
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