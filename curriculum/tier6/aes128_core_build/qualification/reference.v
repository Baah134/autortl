`timescale 1ns/1ps
// Qualification reference only: aes128_core_tb.v must pass this source and
// fail every mutant in mutants.json. Never configured as a generation seed.
// The top below is byte-identical to the harness's mechanical wrapper.
// @latency 1
// Cycle-level iterative sequencer: one key-preparation edge, then ten round edges.
module aes_ctrl (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [127:0] key,
    input wire [127:0] pt,
    output reg out_valid,
    input wire out_ready,
    output reg [127:0] ct,
    output reg [127:0] rk,
    output reg [7:0] rcon,
    output wire last,
    input wire [127:0] round_out,
    input wire [127:0] key_next
);
    reg busy;
    reg [3:0] rnd;

    assign in_ready = !busy && !out_valid;
    assign last = rnd == 4'd10;
    always @(*) begin
        case (rnd)
            4'd0: rcon = 8'h01;
            4'd1: rcon = 8'h02;
            4'd2: rcon = 8'h04;
            4'd3: rcon = 8'h08;
            4'd4: rcon = 8'h10;
            4'd5: rcon = 8'h20;
            4'd6: rcon = 8'h40;
            4'd7: rcon = 8'h80;
            4'd8: rcon = 8'h1b;
            4'd9: rcon = 8'h36;
            default: rcon = 8'h00;
        endcase
    end

    always @(posedge clk) begin // ctrl_clock
        if (rst) begin
            busy <= 1'b0;
            out_valid <= 1'b0;
            rnd <= 4'd0;
            ct <= 128'd0;
            rk <= 128'd0;
        end else if (busy) begin
            rk <= key_next;
            if (rnd == 4'd0) begin
                rnd <= 4'd1;
            end else begin
                ct <= round_out;
                if (rnd == 4'd10) begin
                    busy <= 1'b0;
                    out_valid <= 1'b1;
                    rnd <= 4'd0;
                end else begin
                    rnd <= rnd + 4'd1;
                end
            end
        end else if (out_valid) begin
            if (out_ready) out_valid <= 1'b0;
        end else if (in_valid) begin
            ct <= pt ^ key; // initial_add_round_key
            rk <= key;
            rnd <= 4'd0;
            busy <= 1'b1;
        end
    end
endmodule

// @latency 0
// Combinational AES round: SubBytes, ShiftRows, MixColumns (skipped when final_round), AddRoundKey.
module aes_round (
    input wire [127:0] state_in,
    input wire [127:0] round_key,
    input wire final_round,
    output wire [127:0] state_out
);
    function [7:0] sbox;
        input [7:0] a;
        begin
            case (a)
                8'h00: sbox = 8'h63;
                8'h01: sbox = 8'h7c;
                8'h02: sbox = 8'h77;
                8'h03: sbox = 8'h7b;
                8'h04: sbox = 8'hf2;
                8'h05: sbox = 8'h6b;
                8'h06: sbox = 8'h6f;
                8'h07: sbox = 8'hc5;
                8'h08: sbox = 8'h30;
                8'h09: sbox = 8'h01;
                8'h0a: sbox = 8'h67;
                8'h0b: sbox = 8'h2b;
                8'h0c: sbox = 8'hfe;
                8'h0d: sbox = 8'hd7;
                8'h0e: sbox = 8'hab;
                8'h0f: sbox = 8'h76;
                8'h10: sbox = 8'hca;
                8'h11: sbox = 8'h82;
                8'h12: sbox = 8'hc9;
                8'h13: sbox = 8'h7d;
                8'h14: sbox = 8'hfa;
                8'h15: sbox = 8'h59;
                8'h16: sbox = 8'h47;
                8'h17: sbox = 8'hf0;
                8'h18: sbox = 8'had;
                8'h19: sbox = 8'hd4;
                8'h1a: sbox = 8'ha2;
                8'h1b: sbox = 8'haf;
                8'h1c: sbox = 8'h9c;
                8'h1d: sbox = 8'ha4;
                8'h1e: sbox = 8'h72;
                8'h1f: sbox = 8'hc0;
                8'h20: sbox = 8'hb7;
                8'h21: sbox = 8'hfd;
                8'h22: sbox = 8'h93;
                8'h23: sbox = 8'h26;
                8'h24: sbox = 8'h36;
                8'h25: sbox = 8'h3f;
                8'h26: sbox = 8'hf7;
                8'h27: sbox = 8'hcc;
                8'h28: sbox = 8'h34;
                8'h29: sbox = 8'ha5;
                8'h2a: sbox = 8'he5;
                8'h2b: sbox = 8'hf1;
                8'h2c: sbox = 8'h71;
                8'h2d: sbox = 8'hd8;
                8'h2e: sbox = 8'h31;
                8'h2f: sbox = 8'h15;
                8'h30: sbox = 8'h04;
                8'h31: sbox = 8'hc7;
                8'h32: sbox = 8'h23;
                8'h33: sbox = 8'hc3;
                8'h34: sbox = 8'h18;
                8'h35: sbox = 8'h96;
                8'h36: sbox = 8'h05;
                8'h37: sbox = 8'h9a;
                8'h38: sbox = 8'h07;
                8'h39: sbox = 8'h12;
                8'h3a: sbox = 8'h80;
                8'h3b: sbox = 8'he2;
                8'h3c: sbox = 8'heb;
                8'h3d: sbox = 8'h27;
                8'h3e: sbox = 8'hb2;
                8'h3f: sbox = 8'h75;
                8'h40: sbox = 8'h09;
                8'h41: sbox = 8'h83;
                8'h42: sbox = 8'h2c;
                8'h43: sbox = 8'h1a;
                8'h44: sbox = 8'h1b;
                8'h45: sbox = 8'h6e;
                8'h46: sbox = 8'h5a;
                8'h47: sbox = 8'ha0;
                8'h48: sbox = 8'h52;
                8'h49: sbox = 8'h3b;
                8'h4a: sbox = 8'hd6;
                8'h4b: sbox = 8'hb3;
                8'h4c: sbox = 8'h29;
                8'h4d: sbox = 8'he3;
                8'h4e: sbox = 8'h2f;
                8'h4f: sbox = 8'h84;
                8'h50: sbox = 8'h53;
                8'h51: sbox = 8'hd1;
                8'h52: sbox = 8'h00;
                8'h53: sbox = 8'hed;
                8'h54: sbox = 8'h20;
                8'h55: sbox = 8'hfc;
                8'h56: sbox = 8'hb1;
                8'h57: sbox = 8'h5b;
                8'h58: sbox = 8'h6a;
                8'h59: sbox = 8'hcb;
                8'h5a: sbox = 8'hbe;
                8'h5b: sbox = 8'h39;
                8'h5c: sbox = 8'h4a;
                8'h5d: sbox = 8'h4c;
                8'h5e: sbox = 8'h58;
                8'h5f: sbox = 8'hcf;
                8'h60: sbox = 8'hd0;
                8'h61: sbox = 8'hef;
                8'h62: sbox = 8'haa;
                8'h63: sbox = 8'hfb;
                8'h64: sbox = 8'h43;
                8'h65: sbox = 8'h4d;
                8'h66: sbox = 8'h33;
                8'h67: sbox = 8'h85;
                8'h68: sbox = 8'h45;
                8'h69: sbox = 8'hf9;
                8'h6a: sbox = 8'h02;
                8'h6b: sbox = 8'h7f;
                8'h6c: sbox = 8'h50;
                8'h6d: sbox = 8'h3c;
                8'h6e: sbox = 8'h9f;
                8'h6f: sbox = 8'ha8;
                8'h70: sbox = 8'h51;
                8'h71: sbox = 8'ha3;
                8'h72: sbox = 8'h40;
                8'h73: sbox = 8'h8f;
                8'h74: sbox = 8'h92;
                8'h75: sbox = 8'h9d;
                8'h76: sbox = 8'h38;
                8'h77: sbox = 8'hf5;
                8'h78: sbox = 8'hbc;
                8'h79: sbox = 8'hb6;
                8'h7a: sbox = 8'hda;
                8'h7b: sbox = 8'h21;
                8'h7c: sbox = 8'h10;
                8'h7d: sbox = 8'hff;
                8'h7e: sbox = 8'hf3;
                8'h7f: sbox = 8'hd2;
                8'h80: sbox = 8'hcd;
                8'h81: sbox = 8'h0c;
                8'h82: sbox = 8'h13;
                8'h83: sbox = 8'hec;
                8'h84: sbox = 8'h5f;
                8'h85: sbox = 8'h97;
                8'h86: sbox = 8'h44;
                8'h87: sbox = 8'h17;
                8'h88: sbox = 8'hc4;
                8'h89: sbox = 8'ha7;
                8'h8a: sbox = 8'h7e;
                8'h8b: sbox = 8'h3d;
                8'h8c: sbox = 8'h64;
                8'h8d: sbox = 8'h5d;
                8'h8e: sbox = 8'h19;
                8'h8f: sbox = 8'h73;
                8'h90: sbox = 8'h60;
                8'h91: sbox = 8'h81;
                8'h92: sbox = 8'h4f;
                8'h93: sbox = 8'hdc;
                8'h94: sbox = 8'h22;
                8'h95: sbox = 8'h2a;
                8'h96: sbox = 8'h90;
                8'h97: sbox = 8'h88;
                8'h98: sbox = 8'h46;
                8'h99: sbox = 8'hee;
                8'h9a: sbox = 8'hb8;
                8'h9b: sbox = 8'h14;
                8'h9c: sbox = 8'hde;
                8'h9d: sbox = 8'h5e;
                8'h9e: sbox = 8'h0b;
                8'h9f: sbox = 8'hdb;
                8'ha0: sbox = 8'he0;
                8'ha1: sbox = 8'h32;
                8'ha2: sbox = 8'h3a;
                8'ha3: sbox = 8'h0a;
                8'ha4: sbox = 8'h49;
                8'ha5: sbox = 8'h06;
                8'ha6: sbox = 8'h24;
                8'ha7: sbox = 8'h5c;
                8'ha8: sbox = 8'hc2;
                8'ha9: sbox = 8'hd3;
                8'haa: sbox = 8'hac;
                8'hab: sbox = 8'h62;
                8'hac: sbox = 8'h91;
                8'had: sbox = 8'h95;
                8'hae: sbox = 8'he4;
                8'haf: sbox = 8'h79;
                8'hb0: sbox = 8'he7;
                8'hb1: sbox = 8'hc8;
                8'hb2: sbox = 8'h37;
                8'hb3: sbox = 8'h6d;
                8'hb4: sbox = 8'h8d;
                8'hb5: sbox = 8'hd5;
                8'hb6: sbox = 8'h4e;
                8'hb7: sbox = 8'ha9;
                8'hb8: sbox = 8'h6c;
                8'hb9: sbox = 8'h56;
                8'hba: sbox = 8'hf4;
                8'hbb: sbox = 8'hea;
                8'hbc: sbox = 8'h65;
                8'hbd: sbox = 8'h7a;
                8'hbe: sbox = 8'hae;
                8'hbf: sbox = 8'h08;
                8'hc0: sbox = 8'hba;
                8'hc1: sbox = 8'h78;
                8'hc2: sbox = 8'h25;
                8'hc3: sbox = 8'h2e;
                8'hc4: sbox = 8'h1c;
                8'hc5: sbox = 8'ha6;
                8'hc6: sbox = 8'hb4;
                8'hc7: sbox = 8'hc6;
                8'hc8: sbox = 8'he8;
                8'hc9: sbox = 8'hdd;
                8'hca: sbox = 8'h74;
                8'hcb: sbox = 8'h1f;
                8'hcc: sbox = 8'h4b;
                8'hcd: sbox = 8'hbd;
                8'hce: sbox = 8'h8b;
                8'hcf: sbox = 8'h8a;
                8'hd0: sbox = 8'h70;
                8'hd1: sbox = 8'h3e;
                8'hd2: sbox = 8'hb5;
                8'hd3: sbox = 8'h66;
                8'hd4: sbox = 8'h48;
                8'hd5: sbox = 8'h03;
                8'hd6: sbox = 8'hf6;
                8'hd7: sbox = 8'h0e;
                8'hd8: sbox = 8'h61;
                8'hd9: sbox = 8'h35;
                8'hda: sbox = 8'h57;
                8'hdb: sbox = 8'hb9;
                8'hdc: sbox = 8'h86;
                8'hdd: sbox = 8'hc1;
                8'hde: sbox = 8'h1d;
                8'hdf: sbox = 8'h9e;
                8'he0: sbox = 8'he1;
                8'he1: sbox = 8'hf8;
                8'he2: sbox = 8'h98;
                8'he3: sbox = 8'h11;
                8'he4: sbox = 8'h69;
                8'he5: sbox = 8'hd9;
                8'he6: sbox = 8'h8e;
                8'he7: sbox = 8'h94;
                8'he8: sbox = 8'h9b;
                8'he9: sbox = 8'h1e;
                8'hea: sbox = 8'h87;
                8'heb: sbox = 8'he9;
                8'hec: sbox = 8'hce;
                8'hed: sbox = 8'h55;
                8'hee: sbox = 8'h28;
                8'hef: sbox = 8'hdf;
                8'hf0: sbox = 8'h8c;
                8'hf1: sbox = 8'ha1;
                8'hf2: sbox = 8'h89;
                8'hf3: sbox = 8'h0d;
                8'hf4: sbox = 8'hbf;
                8'hf5: sbox = 8'he6;
                8'hf6: sbox = 8'h42;
                8'hf7: sbox = 8'h68;
                8'hf8: sbox = 8'h41;
                8'hf9: sbox = 8'h99;
                8'hfa: sbox = 8'h2d;
                8'hfb: sbox = 8'h0f;
                8'hfc: sbox = 8'hb0;
                8'hfd: sbox = 8'h54;
                8'hfe: sbox = 8'hbb;
                default: sbox = 8'h16;
            endcase
        end
    endfunction
    function [7:0] xt;
        input [7:0] a;
        begin
            xt = {a[6:0], 1'b0} ^ (a[7] ? 8'h1b : 8'h00);
        end
    endfunction

    wire [7:0] b [0:15];
    wire [7:0] t [0:15];
    wire [7:0] m [0:15];
    wire [127:0] shifted, mixed;
    genvar n, c;
    generate
        for (n = 0; n < 16; n = n + 1) begin : g_sub
            assign b[n] = sbox(state_in[127 - 8 * n -: 8]);
        end
        for (n = 0; n < 16; n = n + 1) begin : g_shift
            // byte n is row n % 4, column n / 4; row r rotates left by r columns
            assign t[n] = b[(n % 4) + 4 * (((n / 4) + (n % 4)) % 4)];
            assign shifted[127 - 8 * n -: 8] = t[n];
        end
        for (c = 0; c < 4; c = c + 1) begin : g_mix
            assign m[4 * c] = xt(t[4 * c]) ^ xt(t[4 * c + 1]) ^ t[4 * c + 1] ^ t[4 * c + 2] ^ t[4 * c + 3];
            assign m[4 * c + 1] = t[4 * c] ^ xt(t[4 * c + 1]) ^ xt(t[4 * c + 2]) ^ t[4 * c + 2] ^ t[4 * c + 3];
            assign m[4 * c + 2] = t[4 * c] ^ t[4 * c + 1] ^ xt(t[4 * c + 2]) ^ xt(t[4 * c + 3]) ^ t[4 * c + 3];
            assign m[4 * c + 3] = xt(t[4 * c]) ^ t[4 * c] ^ t[4 * c + 1] ^ t[4 * c + 2] ^ xt(t[4 * c + 3]);
            assign mixed[127 - 32 * c -: 32] = {m[4 * c], m[4 * c + 1], m[4 * c + 2], m[4 * c + 3]};
        end
    endgenerate
    assign state_out = (final_round ? shifted : mixed) ^ round_key;
endmodule

// @latency 0
// Combinational AES-128 key-schedule step: next round key from the current one and rcon.
module aes_key_step (
    input wire [127:0] key_in,
    input wire [7:0] rcon,
    output wire [127:0] key_out
);
    function [7:0] sub_byte;
        input [7:0] a;
        begin
            case (a)
                8'h00: sub_byte = 8'h63;
                8'h01: sub_byte = 8'h7c;
                8'h02: sub_byte = 8'h77;
                8'h03: sub_byte = 8'h7b;
                8'h04: sub_byte = 8'hf2;
                8'h05: sub_byte = 8'h6b;
                8'h06: sub_byte = 8'h6f;
                8'h07: sub_byte = 8'hc5;
                8'h08: sub_byte = 8'h30;
                8'h09: sub_byte = 8'h01;
                8'h0a: sub_byte = 8'h67;
                8'h0b: sub_byte = 8'h2b;
                8'h0c: sub_byte = 8'hfe;
                8'h0d: sub_byte = 8'hd7;
                8'h0e: sub_byte = 8'hab;
                8'h0f: sub_byte = 8'h76;
                8'h10: sub_byte = 8'hca;
                8'h11: sub_byte = 8'h82;
                8'h12: sub_byte = 8'hc9;
                8'h13: sub_byte = 8'h7d;
                8'h14: sub_byte = 8'hfa;
                8'h15: sub_byte = 8'h59;
                8'h16: sub_byte = 8'h47;
                8'h17: sub_byte = 8'hf0;
                8'h18: sub_byte = 8'had;
                8'h19: sub_byte = 8'hd4;
                8'h1a: sub_byte = 8'ha2;
                8'h1b: sub_byte = 8'haf;
                8'h1c: sub_byte = 8'h9c;
                8'h1d: sub_byte = 8'ha4;
                8'h1e: sub_byte = 8'h72;
                8'h1f: sub_byte = 8'hc0;
                8'h20: sub_byte = 8'hb7;
                8'h21: sub_byte = 8'hfd;
                8'h22: sub_byte = 8'h93;
                8'h23: sub_byte = 8'h26;
                8'h24: sub_byte = 8'h36;
                8'h25: sub_byte = 8'h3f;
                8'h26: sub_byte = 8'hf7;
                8'h27: sub_byte = 8'hcc;
                8'h28: sub_byte = 8'h34;
                8'h29: sub_byte = 8'ha5;
                8'h2a: sub_byte = 8'he5;
                8'h2b: sub_byte = 8'hf1;
                8'h2c: sub_byte = 8'h71;
                8'h2d: sub_byte = 8'hd8;
                8'h2e: sub_byte = 8'h31;
                8'h2f: sub_byte = 8'h15;
                8'h30: sub_byte = 8'h04;
                8'h31: sub_byte = 8'hc7;
                8'h32: sub_byte = 8'h23;
                8'h33: sub_byte = 8'hc3;
                8'h34: sub_byte = 8'h18;
                8'h35: sub_byte = 8'h96;
                8'h36: sub_byte = 8'h05;
                8'h37: sub_byte = 8'h9a;
                8'h38: sub_byte = 8'h07;
                8'h39: sub_byte = 8'h12;
                8'h3a: sub_byte = 8'h80;
                8'h3b: sub_byte = 8'he2;
                8'h3c: sub_byte = 8'heb;
                8'h3d: sub_byte = 8'h27;
                8'h3e: sub_byte = 8'hb2;
                8'h3f: sub_byte = 8'h75;
                8'h40: sub_byte = 8'h09;
                8'h41: sub_byte = 8'h83;
                8'h42: sub_byte = 8'h2c;
                8'h43: sub_byte = 8'h1a;
                8'h44: sub_byte = 8'h1b;
                8'h45: sub_byte = 8'h6e;
                8'h46: sub_byte = 8'h5a;
                8'h47: sub_byte = 8'ha0;
                8'h48: sub_byte = 8'h52;
                8'h49: sub_byte = 8'h3b;
                8'h4a: sub_byte = 8'hd6;
                8'h4b: sub_byte = 8'hb3;
                8'h4c: sub_byte = 8'h29;
                8'h4d: sub_byte = 8'he3;
                8'h4e: sub_byte = 8'h2f;
                8'h4f: sub_byte = 8'h84;
                8'h50: sub_byte = 8'h53;
                8'h51: sub_byte = 8'hd1;
                8'h52: sub_byte = 8'h00;
                8'h53: sub_byte = 8'hed;
                8'h54: sub_byte = 8'h20;
                8'h55: sub_byte = 8'hfc;
                8'h56: sub_byte = 8'hb1;
                8'h57: sub_byte = 8'h5b;
                8'h58: sub_byte = 8'h6a;
                8'h59: sub_byte = 8'hcb;
                8'h5a: sub_byte = 8'hbe;
                8'h5b: sub_byte = 8'h39;
                8'h5c: sub_byte = 8'h4a;
                8'h5d: sub_byte = 8'h4c;
                8'h5e: sub_byte = 8'h58;
                8'h5f: sub_byte = 8'hcf;
                8'h60: sub_byte = 8'hd0;
                8'h61: sub_byte = 8'hef;
                8'h62: sub_byte = 8'haa;
                8'h63: sub_byte = 8'hfb;
                8'h64: sub_byte = 8'h43;
                8'h65: sub_byte = 8'h4d;
                8'h66: sub_byte = 8'h33;
                8'h67: sub_byte = 8'h85;
                8'h68: sub_byte = 8'h45;
                8'h69: sub_byte = 8'hf9;
                8'h6a: sub_byte = 8'h02;
                8'h6b: sub_byte = 8'h7f;
                8'h6c: sub_byte = 8'h50;
                8'h6d: sub_byte = 8'h3c;
                8'h6e: sub_byte = 8'h9f;
                8'h6f: sub_byte = 8'ha8;
                8'h70: sub_byte = 8'h51;
                8'h71: sub_byte = 8'ha3;
                8'h72: sub_byte = 8'h40;
                8'h73: sub_byte = 8'h8f;
                8'h74: sub_byte = 8'h92;
                8'h75: sub_byte = 8'h9d;
                8'h76: sub_byte = 8'h38;
                8'h77: sub_byte = 8'hf5;
                8'h78: sub_byte = 8'hbc;
                8'h79: sub_byte = 8'hb6;
                8'h7a: sub_byte = 8'hda;
                8'h7b: sub_byte = 8'h21;
                8'h7c: sub_byte = 8'h10;
                8'h7d: sub_byte = 8'hff;
                8'h7e: sub_byte = 8'hf3;
                8'h7f: sub_byte = 8'hd2;
                8'h80: sub_byte = 8'hcd;
                8'h81: sub_byte = 8'h0c;
                8'h82: sub_byte = 8'h13;
                8'h83: sub_byte = 8'hec;
                8'h84: sub_byte = 8'h5f;
                8'h85: sub_byte = 8'h97;
                8'h86: sub_byte = 8'h44;
                8'h87: sub_byte = 8'h17;
                8'h88: sub_byte = 8'hc4;
                8'h89: sub_byte = 8'ha7;
                8'h8a: sub_byte = 8'h7e;
                8'h8b: sub_byte = 8'h3d;
                8'h8c: sub_byte = 8'h64;
                8'h8d: sub_byte = 8'h5d;
                8'h8e: sub_byte = 8'h19;
                8'h8f: sub_byte = 8'h73;
                8'h90: sub_byte = 8'h60;
                8'h91: sub_byte = 8'h81;
                8'h92: sub_byte = 8'h4f;
                8'h93: sub_byte = 8'hdc;
                8'h94: sub_byte = 8'h22;
                8'h95: sub_byte = 8'h2a;
                8'h96: sub_byte = 8'h90;
                8'h97: sub_byte = 8'h88;
                8'h98: sub_byte = 8'h46;
                8'h99: sub_byte = 8'hee;
                8'h9a: sub_byte = 8'hb8;
                8'h9b: sub_byte = 8'h14;
                8'h9c: sub_byte = 8'hde;
                8'h9d: sub_byte = 8'h5e;
                8'h9e: sub_byte = 8'h0b;
                8'h9f: sub_byte = 8'hdb;
                8'ha0: sub_byte = 8'he0;
                8'ha1: sub_byte = 8'h32;
                8'ha2: sub_byte = 8'h3a;
                8'ha3: sub_byte = 8'h0a;
                8'ha4: sub_byte = 8'h49;
                8'ha5: sub_byte = 8'h06;
                8'ha6: sub_byte = 8'h24;
                8'ha7: sub_byte = 8'h5c;
                8'ha8: sub_byte = 8'hc2;
                8'ha9: sub_byte = 8'hd3;
                8'haa: sub_byte = 8'hac;
                8'hab: sub_byte = 8'h62;
                8'hac: sub_byte = 8'h91;
                8'had: sub_byte = 8'h95;
                8'hae: sub_byte = 8'he4;
                8'haf: sub_byte = 8'h79;
                8'hb0: sub_byte = 8'he7;
                8'hb1: sub_byte = 8'hc8;
                8'hb2: sub_byte = 8'h37;
                8'hb3: sub_byte = 8'h6d;
                8'hb4: sub_byte = 8'h8d;
                8'hb5: sub_byte = 8'hd5;
                8'hb6: sub_byte = 8'h4e;
                8'hb7: sub_byte = 8'ha9;
                8'hb8: sub_byte = 8'h6c;
                8'hb9: sub_byte = 8'h56;
                8'hba: sub_byte = 8'hf4;
                8'hbb: sub_byte = 8'hea;
                8'hbc: sub_byte = 8'h65;
                8'hbd: sub_byte = 8'h7a;
                8'hbe: sub_byte = 8'hae;
                8'hbf: sub_byte = 8'h08;
                8'hc0: sub_byte = 8'hba;
                8'hc1: sub_byte = 8'h78;
                8'hc2: sub_byte = 8'h25;
                8'hc3: sub_byte = 8'h2e;
                8'hc4: sub_byte = 8'h1c;
                8'hc5: sub_byte = 8'ha6;
                8'hc6: sub_byte = 8'hb4;
                8'hc7: sub_byte = 8'hc6;
                8'hc8: sub_byte = 8'he8;
                8'hc9: sub_byte = 8'hdd;
                8'hca: sub_byte = 8'h74;
                8'hcb: sub_byte = 8'h1f;
                8'hcc: sub_byte = 8'h4b;
                8'hcd: sub_byte = 8'hbd;
                8'hce: sub_byte = 8'h8b;
                8'hcf: sub_byte = 8'h8a;
                8'hd0: sub_byte = 8'h70;
                8'hd1: sub_byte = 8'h3e;
                8'hd2: sub_byte = 8'hb5;
                8'hd3: sub_byte = 8'h66;
                8'hd4: sub_byte = 8'h48;
                8'hd5: sub_byte = 8'h03;
                8'hd6: sub_byte = 8'hf6;
                8'hd7: sub_byte = 8'h0e;
                8'hd8: sub_byte = 8'h61;
                8'hd9: sub_byte = 8'h35;
                8'hda: sub_byte = 8'h57;
                8'hdb: sub_byte = 8'hb9;
                8'hdc: sub_byte = 8'h86;
                8'hdd: sub_byte = 8'hc1;
                8'hde: sub_byte = 8'h1d;
                8'hdf: sub_byte = 8'h9e;
                8'he0: sub_byte = 8'he1;
                8'he1: sub_byte = 8'hf8;
                8'he2: sub_byte = 8'h98;
                8'he3: sub_byte = 8'h11;
                8'he4: sub_byte = 8'h69;
                8'he5: sub_byte = 8'hd9;
                8'he6: sub_byte = 8'h8e;
                8'he7: sub_byte = 8'h94;
                8'he8: sub_byte = 8'h9b;
                8'he9: sub_byte = 8'h1e;
                8'hea: sub_byte = 8'h87;
                8'heb: sub_byte = 8'he9;
                8'hec: sub_byte = 8'hce;
                8'hed: sub_byte = 8'h55;
                8'hee: sub_byte = 8'h28;
                8'hef: sub_byte = 8'hdf;
                8'hf0: sub_byte = 8'h8c;
                8'hf1: sub_byte = 8'ha1;
                8'hf2: sub_byte = 8'h89;
                8'hf3: sub_byte = 8'h0d;
                8'hf4: sub_byte = 8'hbf;
                8'hf5: sub_byte = 8'he6;
                8'hf6: sub_byte = 8'h42;
                8'hf7: sub_byte = 8'h68;
                8'hf8: sub_byte = 8'h41;
                8'hf9: sub_byte = 8'h99;
                8'hfa: sub_byte = 8'h2d;
                8'hfb: sub_byte = 8'h0f;
                8'hfc: sub_byte = 8'hb0;
                8'hfd: sub_byte = 8'h54;
                8'hfe: sub_byte = 8'hbb;
                default: sub_byte = 8'h16;
            endcase
        end
    endfunction
    wire [31:0] w0 = key_in[127:96];
    wire [31:0] w1 = key_in[95:64];
    wire [31:0] w2 = key_in[63:32];
    wire [31:0] w3 = key_in[31:0];
    wire [31:0] rot = {w3[23:0], w3[31:24]};
    wire [31:0] temp = {sub_byte(rot[31:24]) ^ rcon, sub_byte(rot[23:16]), sub_byte(rot[15:8]), sub_byte(rot[7:0])};
    wire [31:0] w4 = w0 ^ temp;
    wire [31:0] w5 = w1 ^ w4;
    wire [31:0] w6 = w2 ^ w5;
    wire [31:0] w7 = w3 ^ w6;
    assign key_out = {w4, w5, w6, w7};
endmodule

`timescale 1ns/1ps
module aes128_core (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [127:0] key,
    input wire [127:0] pt,
    output wire out_valid,
    input wire out_ready,
    output wire [127:0] ct
);
    wire [127:0] w_aes_ctrl_ct;
    wire [127:0] w_aes_ctrl_rk;
    wire w_aes_ctrl_last;
    wire [127:0] w_aes_round_state_out;
    wire [7:0] w_aes_ctrl_rcon;
    wire [127:0] w_aes_key_step_key_out;
    assign ct = w_aes_ctrl_ct;
    aes_ctrl u_aes_ctrl (
        .clk(clk),
        .rst(rst),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .key(key),
        .pt(pt),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .ct(w_aes_ctrl_ct),
        .rk(w_aes_ctrl_rk),
        .rcon(w_aes_ctrl_rcon),
        .last(w_aes_ctrl_last),
        .round_out(w_aes_round_state_out),
        .key_next(w_aes_key_step_key_out)
    );
    aes_round u_aes_round (
        .state_in(w_aes_ctrl_ct),
        .round_key(w_aes_ctrl_rk),
        .final_round(w_aes_ctrl_last),
        .state_out(w_aes_round_state_out)
    );
    aes_key_step u_aes_key_step (
        .key_in(w_aes_ctrl_rk),
        .rcon(w_aes_ctrl_rcon),
        .key_out(w_aes_key_step_key_out)
    );
endmodule
