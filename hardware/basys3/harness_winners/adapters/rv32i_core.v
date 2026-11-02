`timescale 1ns / 1ps
`default_nettype none
// Adapter: rv32i_core (harness winner, unedited). The winner is a multi-cycle
// CPU with a program-load port, a run input and a trace of every
// architectural effect, but no handshake. The adapter runs one program per
// transaction through those ports:
//   1. accept the 8-word program (in_ready only while idle)
//   2. reset the core for one clock (its synchronous reset clears the
//      instruction memory, data memory and registers)
//   3. write words 0..7 through the load port with run low (words 8..63 stay
//      zero, which the core executes as no-operations)
//   4. raise run until the core retires RETIRES instructions
//   5. hold the result until out_ready
// While the program runs, the adapter folds the trace into a signature and
// mirrors the register writes to x1..x6:
//   store (dmem_we, in M):  sig = fold(fold(sig, dmem_addr), dmem_wdata)
//   retire (in W):          sig = fold(sig, pc), then
//                           fold(rf_we ? 32 | rf_waddr : 0) and fold(rf_we ? rf_wdata : 0)
// where fold(s, w) = rotate_left(s, 5) ^ w. A core that never retires ends
// at CYCLE_LIMIT, so a fault shows as a wrong result, not a hung board.
// in_word  bytes 4n..4n+3 = instruction word n, n = 0..7
// out_word bytes 0..3 = signature, bytes 4..7 = cycles from run to the last
//          retirement inclusive, bytes 8..31 = x1..x6 (each least significant
//          byte first)
module stream_dut (
    input  wire         clk,
    input  wire         rst,
    input  wire [255:0] in_word,
    input  wire         in_valid,
    output wire         in_ready,
    output wire [255:0] out_word,
    output wire         out_valid,
    input  wire         out_ready
);
    localparam [5:0]  RETIRES     = 6'd32;
    localparam [15:0] CYCLE_LIMIT = 16'd1023;

    localparam [2:0] S_IDLE  = 3'd0;
    localparam [2:0] S_RESET = 3'd1;
    localparam [2:0] S_LOAD  = 3'd2;
    localparam [2:0] S_EXEC  = 3'd3;
    localparam [2:0] S_DONE  = 3'd4;

    reg  [2:0]   state;
    reg  [255:0] prog_words;       // shifts down one word per load cycle
    reg  [2:0]   load_index;
    reg  [5:0]   retired;
    reg  [15:0]  cycles;
    reg  [31:0]  sig;
    reg  [31:0]  x1, x2, x3, x4, x5, x6;

    wire [31:0] pc, rf_wdata, dmem_wdata;
    wire [4:0]  rf_waddr, dmem_addr;
    wire        retire, rf_we, dmem_we;

    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    rv32i_core u_winner (
        .clk(clk), .rst(rst || state == S_RESET), .run(state == S_EXEC),
        .imem_we(state == S_LOAD), .imem_waddr({3'd0, load_index}), .imem_wdata(prog_words[31:0]),
        .pc(pc), .retire(retire),
        .rf_we(rf_we), .rf_waddr(rf_waddr), .rf_wdata(rf_wdata),
        .dmem_we(dmem_we), .dmem_addr(dmem_addr), .dmem_wdata(dmem_wdata)
    );

    function [31:0] fold(input [31:0] s, input [31:0] w);
        fold = {s[26:0], s[31:27]} ^ w;
    endfunction

    wire [31:0] sig_store  = dmem_we ? fold(fold(sig, {27'd0, dmem_addr}), dmem_wdata) : sig;
    wire [31:0] sig_retire = fold(fold(fold(sig_store, pc),
                                       rf_we ? {26'd0, 1'b1, rf_waddr} : 32'd0),
                                  rf_we ? rf_wdata : 32'd0);
    wire [31:0] sig_next   = retire ? sig_retire : sig_store;
    wire        last       = (retire && retired == RETIRES - 6'd1) || cycles == CYCLE_LIMIT - 16'd1;

    assign in_ready  = state == S_IDLE;
    assign out_valid = state == S_DONE;
    assign out_word  = {x6, x5, x4, x3, x2, x1, 16'd0, cycles, sig};

    always @(posedge clk) begin
        if (rst) begin
            state      <= S_IDLE;
            prog_words <= 256'd0;
            load_index <= 3'd0;
            retired    <= 6'd0;
            cycles     <= 16'd0;
            sig        <= 32'd0;
            x1 <= 32'd0; x2 <= 32'd0; x3 <= 32'd0; x4 <= 32'd0; x5 <= 32'd0; x6 <= 32'd0;
        end else begin
            case (state)
                S_IDLE: if (in_valid) begin
                    prog_words <= in_word;
                    load_index <= 3'd0;
                    retired    <= 6'd0;
                    cycles     <= 16'd0;
                    sig        <= 32'd0;
                    x1 <= 32'd0; x2 <= 32'd0; x3 <= 32'd0; x4 <= 32'd0; x5 <= 32'd0; x6 <= 32'd0;
                    state      <= S_RESET;
                end
                S_RESET: state <= S_LOAD;
                S_LOAD: begin
                    prog_words <= prog_words >> 32;
                    load_index <= load_index + 3'd1;
                    if (load_index == 3'd7) state <= S_EXEC;
                end
                S_EXEC: begin
                    cycles <= cycles + 16'd1;
                    sig    <= sig_next;
                    if (retire) retired <= retired + 6'd1;
                    if (rf_we) begin
                        case (rf_waddr)
                            5'd1: x1 <= rf_wdata;
                            5'd2: x2 <= rf_wdata;
                            5'd3: x3 <= rf_wdata;
                            5'd4: x4 <= rf_wdata;
                            5'd5: x5 <= rf_wdata;
                            5'd6: x6 <= rf_wdata;
                            default: ;
                        endcase
                    end
                    if (last) state <= S_DONE;
                end
                S_DONE: if (out_ready) state <= S_IDLE;
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
`default_nettype wire
