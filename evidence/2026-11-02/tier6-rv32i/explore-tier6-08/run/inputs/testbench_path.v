`timescale 1ns/1ps
// Independent ISA-level and cycle-exact checker for the multi-cycle RV32I core.
// It keeps its own architectural state (pc, x0..x31, 32 data words, the
// instruction image it loaded), executes each instruction from the RV32I
// definition when the core fetches it, and checks every port before each rising
// edge: retire and the register write in W, the store in M, pc always, and the
// exact cycle count of every instruction (4, store 5, load 6, plus fetch
// cycles held by run = 0). Programs: four hand-assembled ones (ALU and
// immediate corner cases, Fibonacci with a sum loop, memory fill and copy with
// address aliasing, every branch taken and not taken plus JAL/JALR links) and
// forty seeded random programs with forward-only control flow. Stimulus never
// depends on DUT outputs and the checker never reads DUT internals.
module rv32i_core_tb;
    reg clk=0, rst=1, run=0, imem_we=0;
    reg [5:0] imem_waddr=0;
    reg [31:0] imem_wdata=0;
    wire [31:0] pc, rf_wdata, dmem_wdata;
    wire retire, rf_we, dmem_we;
    wire [4:0] rf_waddr, dmem_addr;
    rv32i_core dut(.clk(clk),.rst(rst),.run(run),.imem_we(imem_we),.imem_waddr(imem_waddr),
        .imem_wdata(imem_wdata),.pc(pc),.retire(retire),.rf_we(rf_we),.rf_waddr(rf_waddr),
        .rf_wdata(rf_wdata),.dmem_we(dmem_we),.dmem_addr(dmem_addr),.dmem_wdata(dmem_wdata));
    always #5 clk=~clk;

    localparam P_F=0, P_D=1, P_E=2, P_M=3, P_L=4, P_W=5;
    // Reference state.
    reg [31:0] img [0:63];   // image the next program load writes
    reg [31:0] im [0:63];    // instruction memory as written through the load port
    reg [31:0] xr [0:31];
    reg [31:0] dm [0:31];
    reg [31:0] mpc=0;
    integer ph=0;
    // The instruction in flight, executed from the RV32I definition at its fetch edge.
    reg [31:0] ins=0, e_val=0, e_npc=0, e_sdata=0;
    reg [4:0] e_rd=0, e_saddr=0;
    reg e_wb=0, e_ld=0, e_st=0;
    integer e_cls=0;
    integer cov [0:47];
    integer cycle=0, errors=0, started=0, halts=0, retired=0, in_run=0, i, n, mr;
    integer f_stalls=0, idle_run_low=0, busy_resets=0, pulses=0, x0_writes=0, programs=0;
    reg [31:0] seed=32'h6b8b4567;

    task fail;
        input [511:0] rule;
        begin
            errors=errors+1;
            if(errors<=40) $display("FAIL BEHAVIOR rule=%0s cycle=%0d pc=%h",rule,cycle,mpc);
        end
    endtask
    task checker_fail;
        input [511:0] rule;
        begin errors=errors+1; $display("CHECKER_FAIL rule=%0s cycle=%0d",rule,cycle); end
    endtask
    task coverage_fail;
        input [511:0] rule;
        begin errors=errors+1; $display("COVERAGE_FAIL rule=%0s",rule); end
    endtask

    function [31:0] advance;
        input [31:0] v;
        reg [31:0] x;
        begin x=v^(v<<13); x=x^(x>>17); advance=x^(x<<5); end
    endfunction

    // RV32I encoders for the random program generator.
    function [31:0] enc_r;
        input [6:0] f7; input [2:0] f3; input [4:0] rd, rs1, rs2;
        enc_r={f7,rs2,rs1,f3,rd,7'b0110011};
    endfunction
    function [31:0] enc_i;
        input [11:0] imm; input [2:0] f3; input [6:0] op; input [4:0] rd, rs1;
        enc_i={imm,rs1,f3,rd,op};
    endfunction
    function [31:0] enc_s;
        input [11:0] imm; input [4:0] rs1, rs2;
        enc_s={imm[11:5],rs2,rs1,3'b010,imm[4:0],7'b0100011};
    endfunction
    function [31:0] enc_b;
        input [12:0] off; input [2:0] f3; input [4:0] rs1, rs2;
        enc_b={off[12],off[10:5],rs2,rs1,f3,off[4:1],off[11],7'b1100011};
    endfunction
    function [31:0] enc_j;
        input [20:0] off; input [4:0] rd;
        enc_j={off[20],off[10:1],off[11],off[19:12],rd,7'b1101111};
    endfunction

    task model_reset;
        begin
            for(mr=0;mr<32;mr=mr+1) begin xr[mr]=0; dm[mr]=0; end
            for(mr=0;mr<64;mr=mr+1) im[mr]=0;
            mpc=0; ph=P_F; e_wb=0; e_ld=0; e_st=0;
        end
    endtask

    // Execute the instruction at mpc from the ISA definition (word loads and
    // stores, address bits [6:2] select one of 32 data words, bits [1:0] are
    // ignored; FENCE, SYSTEM and unknown opcodes do nothing; funct3 010 and 011
    // branches are never taken). Effects are committed at retirement.
    task fetch_execute;
        reg [6:0] op;
        reg [2:0] f3;
        reg [31:0] a, b, imm_i, imm_s, ea;
        reg t;
        begin
            ins=im[mpc[7:2]];
            op=ins[6:0]; f3=ins[14:12];
            a=xr[ins[19:15]]; b=xr[ins[24:20]];
            imm_i={{20{ins[31]}},ins[31:20]};
            imm_s={{20{ins[31]}},ins[31:25],ins[11:7]};
            e_rd=ins[11:7]; e_wb=0; e_ld=0; e_st=0; e_val=0; e_sdata=0; e_saddr=0;
            e_npc=mpc+32'd4; e_cls=47;
            case(op)
                7'b0110111: begin e_wb=1; e_val={ins[31:12],12'd0}; e_cls=20; end
                7'b0010111: begin e_wb=1; e_val=mpc+{ins[31:12],12'd0}; e_cls=21; end
                7'b1101111: begin
                    e_wb=1; e_val=mpc+32'd4; e_cls=22;
                    e_npc=mpc+{{12{ins[31]}},ins[19:12],ins[20],ins[30:21],1'b0};
                end
                7'b1100111: begin e_wb=1; e_val=mpc+32'd4; e_npc=(a+imm_i)&32'hfffffffe; e_cls=23; end
                7'b1100011: begin
                    case(f3)
                        3'd0: t=(a==b);
                        3'd1: t=(a!=b);
                        3'd4: t=($signed(a)<$signed(b));
                        3'd5: t=($signed(a)>=$signed(b));
                        3'd6: t=(a<b);
                        3'd7: t=(a>=b);
                        default: t=0;
                    endcase
                    if(t) e_npc=mpc+{{20{ins[31]}},ins[7],ins[30:25],ins[11:8],1'b0};
                    e_cls=24+2*f3+t;
                end
                7'b0000011: begin e_wb=1; e_ld=1; ea=a+imm_i; e_val=dm[ea[6:2]]; e_cls=40; end
                7'b0100011: begin e_st=1; ea=a+imm_s; e_saddr=ea[6:2]; e_sdata=b; e_cls=41; end
                7'b0010011, 7'b0110011: begin
                    e_wb=1;
                    if(op==7'b0010011) b=imm_i;
                    if(op==7'b0110011) e_cls=(ins[30] && f3==3'd0) ? 8 : (ins[30] && f3==3'd5) ? 9 : f3;
                    else e_cls=(ins[30] && f3==3'd5) ? 18 : 10+f3;
                    case(f3)
                        3'd0: if(op==7'b0110011 && ins[30]) e_val=a-b; else e_val=a+b;
                        3'd1: e_val=a<<b[4:0];
                        3'd2: e_val=($signed(a)<$signed(b)) ? 32'd1 : 32'd0;
                        3'd3: e_val=(a<b) ? 32'd1 : 32'd0;
                        3'd4: e_val=a^b;
                        3'd5: if(ins[30]) e_val=$signed(a)>>>b[4:0]; else e_val=a>>b[4:0];
                        3'd6: e_val=a|b;
                        default: e_val=a&b;
                    endcase
                end
                default: e_cls=42;
            endcase
        end
    endtask

    task check_ports;
        begin
            if(retire !== (ph==P_W)) fail("retire_exactly_in_writeback");
            if(rf_we !== (ph==P_W && e_wb)) fail("rf_we_for_writing_instructions_in_writeback");
            if(ph==P_W && e_wb) begin
                if(rf_waddr !== e_rd) fail("rf_waddr_is_rd");
                if(rf_wdata !== e_val) fail("rf_wdata_is_the_architectural_result");
            end
            if(dmem_we !== (ph==P_M && e_st)) fail("dmem_we_for_stores_in_memory_phase");
            if(ph==P_M && e_st) begin
                if(dmem_addr !== e_saddr) fail("store_word_address");
                if(dmem_wdata !== e_sdata) fail("store_data_is_rs2");
            end
            if(pc !== mpc) fail("pc_of_the_instruction_in_flight");
        end
    endtask

    // Model the contract sequencer at a rising edge with the sampled inputs.
    task clock_edge;
        begin
            if(rst) begin
                if(ph!=P_F || mpc!=0) busy_resets=busy_resets+1;
                model_reset;
            end else begin
                case(ph)
                    P_F: if(run) begin fetch_execute; ph=P_D; end else if(in_run) f_stalls=f_stalls+1;
                    P_D: begin ph=P_E; if(!run) idle_run_low=idle_run_low+1; end
                    P_E: ph=(e_ld || e_st) ? P_M : P_W;
                    P_M: ph=e_ld ? P_L : P_W;
                    P_L: ph=P_W;
                    default: begin
                        if(e_wb && e_rd!=0) xr[e_rd]=e_val;
                        if(e_wb && e_rd==0 && ins!=32'h0000006f) x0_writes=x0_writes+1;
                        if(e_st) dm[e_saddr]=e_sdata;
                        mpc=e_npc; ph=P_F; retired=retired+1;
                        cov[e_cls]=cov[e_cls]+1;
                        if(ins==32'h0000006f) halts=halts+1;
                    end
                endcase
                // The fetch above read the pre-edge image (read-first).
                if(imem_we) im[imem_waddr]=imem_wdata;
            end
        end
    endtask

    // One clock cycle: inputs change at the falling edge, ports are checked
    // before the rising edge; pulse adds an off-edge reset pulse.
    task step;
        input r, rn, we;
        input [5:0] wa;
        input [31:0] wd;
        input pulse;
        begin
            @(negedge clk);
            rst=r; run=rn; imem_we=we; imem_waddr=wa; imem_wdata=wd;
            #1; if(started) check_ports;
            if(pulse) begin #1 rst=1; #2 rst=0; pulses=pulses+1; end
            @(posedge clk);
            cycle=cycle+1;
            clock_edge;
            if(rst) started=1;
        end
    endtask

    task hand_program;
        input integer which;
        begin
            for(n=0;n<64;n=n+1) img[n]=32'h0000006f;
            case(which)
            0: begin // alu
                img[0] = 32'h800000b7; // lui x1, 0x80000
                img[1] = 32'h01008093; // addi x1, x1, 16
                img[2] = 32'hfff00113; // addi x2, x0, -1
                img[3] = 32'h00100193; // addi x3, x0, 1
                img[4] = 32'h00208233; // add x4, x1, x2
                img[5] = 32'h402182b3; // sub x5, x3, x2
                img[6] = 32'h40310333; // sub x6, x2, x3
                img[7] = 32'h0020f3b3; // and x7, x1, x2
                img[8] = 32'h0030e433; // or x8, x1, x3
                img[9] = 32'h0020c4b3; // xor x9, x1, x2
                img[10] = 32'h00312533; // slt x10, x2, x3
                img[11] = 32'h003135b3; // sltu x11, x2, x3
                img[12] = 32'h0021a633; // slt x12, x3, x2
                img[13] = 32'h0021b6b3; // sltu x13, x3, x2
                img[14] = 32'h00400713; // addi x14, x0, 4
                img[15] = 32'h00e097b3; // sll x15, x1, x14
                img[16] = 32'h00e0d833; // srl x16, x1, x14
                img[17] = 32'h40e0d8b3; // sra x17, x1, x14
                img[18] = 32'h02400913; // addi x18, x0, 36
                img[19] = 32'h012199b3; // sll x19, x3, x18
                img[20] = 32'h41215933; // sra x18, x2, x18
                img[21] = 32'h01f11a13; // slli x20, x2, 31
                img[22] = 32'h01f0da93; // srli x21, x1, 31
                img[23] = 32'h41f0db13; // srai x22, x1, 31
                img[24] = 32'h4000db93; // srai x23, x1, 0
                img[25] = 32'h00012c13; // slti x24, x2, 0
                img[26] = 32'hfff1bc93; // sltiu x25, x3, -1
                img[27] = 32'hfff13d13; // sltiu x26, x2, -1
                img[28] = 32'hfff0cd93; // xori x27, x1, -1
                img[29] = 32'h7f01ee13; // ori x28, x3, 0x7f0
                img[30] = 32'h80017e93; // andi x29, x2, -2048
                img[31] = 32'h12345f17; // auipc x30, 0x12345
                img[32] = 32'hffffffb7; // lui x31, 0xfffff
                img[33] = 32'h00500013; // addi x0, x0, 5
                img[34] = 32'h000002b3; // add x5, x0, x0
                img[35] = 32'h7ff00313; // addi x6, x0, 0x7ff
                img[36] = 32'h80000393; // addi x7, x0, -2048
                img[37] = 32'h00730433; // add x8, x6, x7
                img[38] = 32'h401004b3; // sub x9, x0, x1
                img[39] = 32'h0060a533; // slt x10, x1, x6
                img[40] = 32'h0060b5b3; // sltu x11, x1, x6
                img[41] = 32'h00115613; // srli x12, x2, 1
                img[42] = 32'h40115693; // srai x13, x2, 1
                img[43] = 32'h0ff0000f; // .word 0x0ff0000f
                img[44] = 32'h00000073; // .word 0x00000073
                img[45] = 32'h01ff4733; // xor x14, x30, x31
                img[46] = 32'h000067b3; // or x15, x0, x0
                img[47] = 32'h00402023; // sw x4, 0(x0)
                img[48] = 32'h00002803; // lw x16, 0(x0)
                img[49] = 32'h0000006f; // halt
            end
            1: begin // fib
                img[0] = 32'h00000093; // addi x1, x0, 0
                img[1] = 32'h00100113; // addi x2, x0, 1
                img[2] = 32'h00000193; // addi x3, x0, 0
                img[3] = 32'h05000213; // addi x4, x0, 80
                img[4] = 32'h0011a023; // sw x1, 0(x3)
                img[5] = 32'h002082b3; // add x5, x1, x2
                img[6] = 32'h00010093; // addi x1, x2, 0
                img[7] = 32'h00028113; // addi x2, x5, 0
                img[8] = 32'h00418193; // addi x3, x3, 4
                img[9] = 32'hfe41c6e3; // blt x3, x4, fill
                img[10] = 32'h00000193; // addi x3, x0, 0
                img[11] = 32'h00000313; // addi x6, x0, 0
                img[12] = 32'h0001a383; // lw x7, 0(x3)
                img[13] = 32'h00730333; // add x6, x6, x7
                img[14] = 32'h00418193; // addi x3, x3, 4
                img[15] = 32'hfe419ae3; // bne x3, x4, sum
                img[16] = 32'h04602a23; // sw x6, 84(x0)
                img[17] = 32'h04c02403; // lw x8, 76(x0)
                img[18] = 32'h04802483; // lw x9, 72(x0)
                img[19] = 32'h40940533; // sub x10, x8, x9
                img[20] = 32'h0000006f; // halt
            end
            2: begin // memcpy
                img[0] = 32'h012340b7; // lui x1, 0x01234
                img[1] = 32'h56708093; // addi x1, x1, 0x567
                img[2] = 32'h00000113; // addi x2, x0, 0
                img[3] = 32'h02000193; // addi x3, x0, 32
                img[4] = 32'h00112023; // sw x1, 0(x2)
                img[5] = 32'h00209293; // slli x5, x1, 2
                img[6] = 32'h005080b3; // add x1, x1, x5
                img[7] = 32'h5a50c093; // xori x1, x1, 0x5a5
                img[8] = 32'h00410113; // addi x2, x2, 4
                img[9] = 32'hfe3166e3; // bltu x2, x3, fill
                img[10] = 32'h00000113; // addi x2, x0, 0
                img[11] = 32'h04000213; // addi x4, x0, 64
                img[12] = 32'h00012303; // lw x6, 0(x2)
                img[13] = 32'h00622023; // sw x6, 0(x4)
                img[14] = 32'h00410113; // addi x2, x2, 4
                img[15] = 32'h00420213; // addi x4, x4, 4
                img[16] = 32'hfe3118e3; // bne x2, x3, copy
                img[17] = 32'h05c00213; // addi x4, x0, 92
                img[18] = 32'hfe422383; // lw x7, -28(x4)
                img[19] = 32'h00022403; // lw x8, 0(x4)
                img[20] = 32'hfc022483; // lw x9, -64(x4)
                img[21] = 32'h08402503; // lw x10, 132(x0)
                img[22] = 32'h06a02e23; // sw x10, 124(x0)
                img[23] = 32'h0fc02583; // lw x11, 252(x0)
                img[24] = 32'h00602603; // lw x12, 6(x0)
                img[25] = 32'hfec22fa3; // sw x12, -1(x4)
                img[26] = 32'h05802683; // lw x13, 88(x0)
                img[27] = 32'h0000006f; // halt
            end
            3: begin // branch
                img[0] = 32'hfff00093; // addi x1, x0, -1
                img[1] = 32'h00100113; // addi x2, x0, 1
                img[2] = 32'h00100193; // addi x3, x0, 1
                img[3] = 32'hffe00213; // addi x4, x0, -2
                img[4] = 32'h00000513; // addi x10, x0, 0
                img[5] = 32'h00310463; // beq x2, x3, l1
                img[6] = 32'h00150513; // addi x10, x10, 1
                img[7] = 32'h00208463; // beq x1, x2, l2
                img[8] = 32'h00250513; // addi x10, x10, 2
                img[9] = 32'h00209463; // bne x1, x2, l3
                img[10] = 32'h00450513; // addi x10, x10, 4
                img[11] = 32'h00311463; // bne x2, x3, l4
                img[12] = 32'h00850513; // addi x10, x10, 8
                img[13] = 32'h0020c463; // blt x1, x2, l5
                img[14] = 32'h01050513; // addi x10, x10, 16
                img[15] = 32'h00114463; // blt x2, x1, l6
                img[16] = 32'h02050513; // addi x10, x10, 32
                img[17] = 32'h0020e463; // bltu x1, x2, l7
                img[18] = 32'h04050513; // addi x10, x10, 64
                img[19] = 32'h00116463; // bltu x2, x1, l8
                img[20] = 32'h08050513; // addi x10, x10, 128
                img[21] = 32'h00315463; // bge x2, x3, l9
                img[22] = 32'h10050513; // addi x10, x10, 256
                img[23] = 32'h00125463; // bge x4, x1, l10
                img[24] = 32'h20050513; // addi x10, x10, 512
                img[25] = 32'h0020f463; // bgeu x1, x2, l11
                img[26] = 32'h40050513; // addi x10, x10, 1024
                img[27] = 32'h00117463; // bgeu x2, x1, l12
                img[28] = 32'h00750513; // addi x10, x10, 7
                img[29] = 32'h00316c63; // bltu x2, x3, l13
                img[30] = 32'h00312a63; // bx2 x2, x3, l13
                img[31] = 32'h00103863; // bx3 x0, x1, l13
                img[32] = 32'h0040c663; // blt x1, x4, l13
                img[33] = 32'h00127463; // bgeu x4, x1, l13
                img[34] = 32'h00350513; // addi x10, x10, 3
                img[35] = 32'h008002ef; // jal x5, l14
                img[36] = 32'h06450513; // addi x10, x10, 100
                img[37] = 32'h00000317; // auipc x6, 0
                img[38] = 32'h01130313; // addi x6, x6, 17
                img[39] = 32'h000303e7; // jalr x7, 0(x6)
                img[40] = 32'h0c850513; // addi x10, x10, 200
                img[41] = 32'h00300593; // addi x11, x0, 3
                img[42] = 32'hfff58593; // addi x11, x11, -1
                img[43] = 32'h00058463; // beq x11, x0, out
                img[44] = 32'hff9ff06f; // jal x0, back
                img[45] = 32'h018000ef; // jal x1, func
                img[46] = 32'h00a02023; // sw x10, 0(x0)
                img[47] = 32'h00502223; // sw x5, 4(x0)
                img[48] = 32'h00702423; // sw x7, 8(x0)
                img[49] = 32'h01008067; // jalr x0, 16(x1)
                img[50] = 32'h0000006f; // halt
                img[51] = 32'h04050513; // addi x10, x10, 64
                img[52] = 32'h000084e7; // jalr x9, 0(x1)
            end
                default: ;
            endcase
        end
    endtask

    task random_program;
        input [31:0] s0;
        reg [31:0] s, r, v;
        reg [4:0] rd, rs1, rs2;
        reg [2:0] f3;
        reg [12:0] boff;
        integer hop;
        begin
            s=s0;
            for(n=0;n<63;n=n+1) begin
                s=advance(s); r=s; s=advance(s); v=s;
                rd={1'b0,r[8:5]}; rs1={1'b0,r[12:9]}; rs2={1'b0,r[16:13]}; f3=r[19:17];
                hop=1+r[22:21]; if(n+hop>63) hop=63-n;
                if(n<8) begin
                    // Seed x1..x8 with LUI and ADDI so later operations see wide values.
                    if(n%2==0) img[n]={v[31:12],5'd1+n[4:0],7'b0110111};
                    else img[n]=enc_i(v[11:0],3'd0,7'b0010011,5'd1+n[4:0]-5'd1,5'd1+n[4:0]-5'd1);
                end else case(r[3:0])
                    4'd0, 4'd1, 4'd2, 4'd3:
                        img[n]=enc_r(((f3==3'd0 || f3==3'd5) && r[20]) ? 7'h20 : 7'h00, f3, rd, rs1, rs2);
                    4'd4, 4'd5, 4'd6:
                        if(f3==3'd1) img[n]=enc_i({7'd0,v[4:0]},f3,7'b0010011,rd,rs1);
                        else if(f3==3'd5) img[n]=enc_i({1'b0,r[20],5'd0,v[4:0]},f3,7'b0010011,rd,rs1);
                        else img[n]=enc_i(v[11:0],f3,7'b0010011,rd,rs1);
                    4'd7: img[n]={v[31:12],rd,7'b0110111};
                    4'd8: img[n]={v[31:12],rd,7'b0010111};
                    4'd9: img[n]=enc_i(v[11:0],3'b010,7'b0000011,rd,rs1);
                    4'd10: img[n]=enc_s(v[11:0],rs1,rs2);
                    4'd11, 4'd12: begin
                        boff=4*hop;
                        img[n]=enc_b(boff,(f3==3'd2) ? 3'd0 : (f3==3'd3) ? 3'd1 : f3,rs1,rs2);
                    end
                    4'd13: img[n]=enc_j(4*hop,rd);
                    4'd14: img[n]=enc_i(4*(n+hop)+r[23],3'd0,7'b1100111,rd,5'd0);
                    default: case(r[21:20])
                        2'd0: img[n]=32'h0ff0000f;
                        2'd1: img[n]=enc_i(v[11:0],3'd0,7'b0010011,5'd0,rs1);
                        2'd2: img[n]=32'h00000073;
                        default: img[n]={v[31:7],7'b0001011};
                    endcase
                endcase
            end
            img[63]=32'h0000006f;
        end
    endtask

    // Reset the (possibly busy) core, load the image with run low, hold run low
    // for idle cycles, then run until the reference retires the halt loop
    // (jal x0, 0) twice, or abort after a cycle budget for a mid-program reset.
    task run_program;
        input integer stall_mode, abort_after, pulse_at;
        integer c, h0;
        reg rn;
        begin
            programs=programs+1;
            step(1,0,0,6'd0,32'd0,0);
            step(1,0,0,6'd0,32'd0,0);
            for(n=0;n<64;n=n+1) step(0,0,1,n[5:0],img[n],0);
            for(n=0;n<3;n=n+1) step(0,0,0,6'd0,32'd0,0);
            h0=halts; c=0; in_run=1;
            while(halts<h0+2 && c<12000 && (abort_after==0 || c<abort_after)) begin
                seed=advance(seed);
                rn=(stall_mode==0) ? 1'b1 : (seed[2:0]!=3'd0);
                step(0,rn,0,6'd0,32'd0,(c==pulse_at));
                c=c+1;
            end
            in_run=0;
            if(abort_after==0 && halts<h0+2) checker_fail("program_reaches_halt");
        end
    endtask

    integer p, q;
    initial begin
        for(i=0;i<48;i=i+1) cov[i]=0;
        model_reset;
        for(q=0;q<4;q=q+1) begin hand_program(q); run_program(0,0,-1); end
        $display("PROGRESS hand programs done cycle=%0d retired=%0d",cycle,retired);
        // The branch program again with run randomly low in fetch.
        hand_program(3); run_program(1,0,-1);
        for(p=0;p<40;p=p+1) begin
            seed=advance(seed^p);
            random_program(seed ^ (32'h9e3779b9*p));
            run_program(p%2, (p==7) ? 120 : 0, (p==11 || p==23) ? 37 : -1);
        end
        // Finish with a reset of the halted core.
        step(1,0,0,6'd0,32'd0,0);
        step(0,0,0,6'd0,32'd0,0);
        step(0,0,0,6'd0,32'd0,0);
        for(i=0;i<19;i=i+1)
            if(cov[i]<3) coverage_fail("each_register_and_immediate_operation");
        if(cov[20]<3 || cov[21]<3 || cov[22]<3 || cov[23]<3 || cov[40]<20 || cov[41]<20 || cov[42]<3)
            coverage_fail("upper_jump_memory_and_nop");
        for(i=0;i<8;i=i+1)
            if(i!=2 && i!=3 && (cov[24+2*i]<3 || cov[25+2*i]<3)) coverage_fail("each_branch_taken_and_not_taken");
        if(cov[28]<1 || cov[30]<1) coverage_fail("reserved_branch_encodings_not_taken");
        if(x0_writes<3 || f_stalls<100 || idle_run_low<20 || busy_resets<40 || pulses!=2)
            coverage_fail("x0_run_and_resets");
        $display("COVERAGE cycles=%0d programs=%0d retired=%0d halts=%0d loads=%0d stores=%0d nops=%0d x0_writes=%0d f_stalls=%0d run_low_in_decode=%0d busy_resets=%0d pulses=%0d",
            cycle,programs,retired,halts,cov[40],cov[41],cov[42],x0_writes,f_stalls,idle_run_low,busy_resets,pulses);
        if(errors==0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors",errors);
        $finish;
    end
    initial begin
        #5000000;
        $display("TEST FAILED: watchdog timeout");
        $finish;
    end
endmodule
