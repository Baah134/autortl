`timescale 1ns/1ps
// @latency 1
module aes_ctrl (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [127:0] key,
    input wire [127:0] pt,
    output wire out_valid,
    input wire out_ready,
    output wire [127:0] ct,
    output wire [127:0] rk,
    output wire [7:0] rcon,
    output wire last,
    input wire [127:0] round_out,
    input wire [127:0] key_next
);

    reg busy;
    reg out_valid_reg;
    reg [3:0] rnd;
    reg [127:0] ct_reg;
    reg [127:0] rk_reg;

    assign in_ready = !busy && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign ct = ct_reg;
    assign rk = rk_reg;
    assign last = (rnd == 4'd10);

    reg [7:0] rcon_value;
    always @(*) begin
        rcon_value = 8'h00;
        case (rnd)
            4'd0: rcon_value = 8'h01;
            4'd1: rcon_value = 8'h02;
            4'd2: rcon_value = 8'h04;
            4'd3: rcon_value = 8'h08;
            4'd4: rcon_value = 8'h10;
            4'd5: rcon_value = 8'h20;
            4'd6: rcon_value = 8'h40;
            4'd7: rcon_value = 8'h80;
            4'd8: rcon_value = 8'h1b;
            4'd9: rcon_value = 8'h36;
            default: rcon_value = 8'h00;
        endcase
    end
    assign rcon = rcon_value;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b0;
            rnd <= 4'd0;
            ct_reg <= 128'd0;
            rk_reg <= 128'd0;
        end else if (busy) begin
            rk_reg <= key_next;
            if (rnd == 4'd0) begin
                rnd <= 4'd1;
            end else begin
                ct_reg <= round_out;
                if (rnd == 4'd10) begin
                    busy <= 1'b0;
                    out_valid_reg <= 1'b1;
                    rnd <= 4'd0;
                end else begin
                    rnd <= rnd + 1'b1;
                end
            end
        end else if (out_valid_reg) begin
            if (out_ready)
                out_valid_reg <= 1'b0;
        end else if (in_valid) begin
            ct_reg <= pt ^ key;
            rk_reg <= key;
            rnd <= 4'd0;
            busy <= 1'b1;
        end
    end

endmodule

module aes_sbox_lookup (
    input wire [7:0] value,
    output reg [7:0] result
);
    always @(*) begin
        result = 8'h00;
        case (value[7:4])
            4'h0: begin
                case (value[3:0])
                    4'h0: result = 8'h63; 4'h1: result = 8'h7c;
                    4'h2: result = 8'h77; 4'h3: result = 8'h7b;
                    4'h4: result = 8'hf2; 4'h5: result = 8'h6b;
                    4'h6: result = 8'h6f; 4'h7: result = 8'hc5;
                    4'h8: result = 8'h30; 4'h9: result = 8'h01;
                    4'ha: result = 8'h67; 4'hb: result = 8'h2b;
                    4'hc: result = 8'hfe; 4'hd: result = 8'hd7;
                    4'he: result = 8'hab; 4'hf: result = 8'h76;
                endcase
            end
            4'h1: begin
                case (value[3:0])
                    4'h0: result = 8'hca; 4'h1: result = 8'h82;
                    4'h2: result = 8'hc9; 4'h3: result = 8'h7d;
                    4'h4: result = 8'hfa; 4'h5: result = 8'h59;
                    4'h6: result = 8'h47; 4'h7: result = 8'hf0;
                    4'h8: result = 8'had; 4'h9: result = 8'hd4;
                    4'ha: result = 8'ha2; 4'hb: result = 8'haf;
                    4'hc: result = 8'h9c; 4'hd: result = 8'ha4;
                    4'he: result = 8'h72; 4'hf: result = 8'hc0;
                endcase
            end
            4'h2: begin
                case (value[3:0])
                    4'h0: result = 8'hb7; 4'h1: result = 8'hfd;
                    4'h2: result = 8'h93; 4'h3: result = 8'h26;
                    4'h4: result = 8'h36; 4'h5: result = 8'h3f;
                    4'h6: result = 8'hf7; 4'h7: result = 8'hcc;
                    4'h8: result = 8'h34; 4'h9: result = 8'ha5;
                    4'ha: result = 8'he5; 4'hb: result = 8'hf1;
                    4'hc: result = 8'h71; 4'hd: result = 8'hd8;
                    4'he: result = 8'h31; 4'hf: result = 8'h15;
                endcase
            end
            4'h3: begin
                case (value[3:0])
                    4'h0: result = 8'h04; 4'h1: result = 8'hc7;
                    4'h2: result = 8'h23; 4'h3: result = 8'hc3;
                    4'h4: result = 8'h18; 4'h5: result = 8'h96;
                    4'h6: result = 8'h05; 4'h7: result = 8'h9a;
                    4'h8: result = 8'h07; 4'h9: result = 8'h12;
                    4'ha: result = 8'h80; 4'hb: result = 8'he2;
                    4'hc: result = 8'heb; 4'hd: result = 8'h27;
                    4'he: result = 8'hb2; 4'hf: result = 8'h75;
                endcase
            end
            4'h4: begin
                case (value[3:0])
                    4'h0: result = 8'h09; 4'h1: result = 8'h83;
                    4'h2: result = 8'h2c; 4'h3: result = 8'h1a;
                    4'h4: result = 8'h1b; 4'h5: result = 8'h6e;
                    4'h6: result = 8'h5a; 4'h7: result = 8'ha0;
                    4'h8: result = 8'h52; 4'h9: result = 8'h3b;
                    4'ha: result = 8'hd6; 4'hb: result = 8'hb3;
                    4'hc: result = 8'h29; 4'hd: result = 8'he3;
                    4'he: result = 8'h2f; 4'hf: result = 8'h84;
                endcase
            end
            4'h5: begin
                case (value[3:0])
                    4'h0: result = 8'h53; 4'h1: result = 8'hd1;
                    4'h2: result = 8'h00; 4'h3: result = 8'hed;
                    4'h4: result = 8'h20; 4'h5: result = 8'hfc;
                    4'h6: result = 8'hb1; 4'h7: result = 8'h5b;
                    4'h8: result = 8'h6a; 4'h9: result = 8'hcb;
                    4'ha: result = 8'hbe; 4'hb: result = 8'h39;
                    4'hc: result = 8'h4a; 4'hd: result = 8'h4c;
                    4'he: result = 8'h58; 4'hf: result = 8'hcf;
                endcase
            end
            4'h6: begin
                case (value[3:0])
                    4'h0: result = 8'hd0; 4'h1: result = 8'hef;
                    4'h2: result = 8'haa; 4'h3: result = 8'hfb;
                    4'h4: result = 8'h43; 4'h5: result = 8'h4d;
                    4'h6: result = 8'h33; 4'h7: result = 8'h85;
                    4'h8: result = 8'h45; 4'h9: result = 8'hf9;
                    4'ha: result = 8'h02; 4'hb: result = 8'h7f;
                    4'hc: result = 8'h50; 4'hd: result = 8'h3c;
                    4'he: result = 8'h9f; 4'hf: result = 8'ha8;
                endcase
            end
            4'h7: begin
                case (value[3:0])
                    4'h0: result = 8'h51; 4'h1: result = 8'ha3;
                    4'h2: result = 8'h40; 4'h3: result = 8'h8f;
                    4'h4: result = 8'h92; 4'h5: result = 8'h9d;
                    4'h6: result = 8'h38; 4'h7: result = 8'hf5;
                    4'h8: result = 8'hbc; 4'h9: result = 8'hb6;
                    4'ha: result = 8'hda; 4'hb: result = 8'h21;
                    4'hc: result = 8'h10; 4'hd: result = 8'hff;
                    4'he: result = 8'hf3; 4'hf: result = 8'hd2;
                endcase
            end
            4'h8: begin
                case (value[3:0])
                    4'h0: result = 8'hcd; 4'h1: result = 8'h0c;
                    4'h2: result = 8'h13; 4'h3: result = 8'hec;
                    4'h4: result = 8'h5f; 4'h5: result = 8'h97;
                    4'h6: result = 8'h44; 4'h7: result = 8'h17;
                    4'h8: result = 8'hc4; 4'h9: result = 8'ha7;
                    4'ha: result = 8'h7e; 4'hb: result = 8'h3d;
                    4'hc: result = 8'h64; 4'hd: result = 8'h5d;
                    4'he: result = 8'h19; 4'hf: result = 8'h73;
                endcase
            end
            4'h9: begin
                case (value[3:0])
                    4'h0: result = 8'h60; 4'h1: result = 8'h81;
                    4'h2: result = 8'h4f; 4'h3: result = 8'hdc;
                    4'h4: result = 8'h22; 4'h5: result = 8'h2a;
                    4'h6: result = 8'h90; 4'h7: result = 8'h88;
                    4'h8: result = 8'h46; 4'h9: result = 8'hee;
                    4'ha: result = 8'hb8; 4'hb: result = 8'h14;
                    4'hc: result = 8'hde; 4'hd: result = 8'h5e;
                    4'he: result = 8'h0b; 4'hf: result = 8'hdb;
                endcase
            end
            4'ha: begin
                case (value[3:0])
                    4'h0: result = 8'he0; 4'h1: result = 8'h32;
                    4'h2: result = 8'h3a; 4'h3: result = 8'h0a;
                    4'h4: result = 8'h49; 4'h5: result = 8'h06;
                    4'h6: result = 8'h24; 4'h7: result = 8'h5c;
                    4'h8: result = 8'hc2; 4'h9: result = 8'hd3;
                    4'ha: result = 8'hac; 4'hb: result = 8'h62;
                    4'hc: result = 8'h91; 4'hd: result = 8'h95;
                    4'he: result = 8'he4; 4'hf: result = 8'h79;
                endcase
            end
            4'hb: begin
                case (value[3:0])
                    4'h0: result = 8'he7; 4'h1: result = 8'hc8;
                    4'h2: result = 8'h37; 4'h3: result = 8'h6d;
                    4'h4: result = 8'h8d; 4'h5: result = 8'hd5;
                    4'h6: result = 8'h4e; 4'h7: result = 8'ha9;
                    4'h8: result = 8'h6c; 4'h9: result = 8'h56;
                    4'ha: result = 8'hf4; 4'hb: result = 8'hea;
                    4'hc: result = 8'h65; 4'hd: result = 8'h7a;
                    4'he: result = 8'hae; 4'hf: result = 8'h08;
                endcase
            end
            4'hc: begin
                case (value[3:0])
                    4'h0: result = 8'hba; 4'h1: result = 8'h78;
                    4'h2: result = 8'h25; 4'h3: result = 8'h2e;
                    4'h4: result = 8'h1c; 4'h5: result = 8'ha6;
                    4'h6: result = 8'hb4; 4'h7: result = 8'hc6;
                    4'h8: result = 8'he8; 4'h9: result = 8'hdd;
                    4'ha: result = 8'h74; 4'hb: result = 8'h1f;
                    4'hc: result = 8'h4b; 4'hd: result = 8'hbd;
                    4'he: result = 8'h8b; 4'hf: result = 8'h8a;
                endcase
            end
            4'hd: begin
                case (value[3:0])
                    4'h0: result = 8'h70; 4'h1: result = 8'h3e;
                    4'h2: result = 8'hb5; 4'h3: result = 8'h66;
                    4'h4: result = 8'h48; 4'h5: result = 8'h03;
                    4'h6: result = 8'hf6; 4'h7: result = 8'h0e;
                    4'h8: result = 8'h61; 4'h9: result = 8'h35;
                    4'ha: result = 8'h57; 4'hb: result = 8'hb9;
                    4'hc: result = 8'h86; 4'hd: result = 8'hc1;
                    4'he: result = 8'h1d; 4'hf: result = 8'h9e;
                endcase
            end
            4'he: begin
                case (value[3:0])
                    4'h0: result = 8'he1; 4'h1: result = 8'hf8;
                    4'h2: result = 8'h98; 4'h3: result = 8'h11;
                    4'h4: result = 8'h69; 4'h5: result = 8'hd9;
                    4'h6: result = 8'h8e; 4'h7: result = 8'h94;
                    4'h8: result = 8'h9b; 4'h9: result = 8'h1e;
                    4'ha: result = 8'h87; 4'hb: result = 8'he9;
                    4'hc: result = 8'hce; 4'hd: result = 8'h55;
                    4'he: result = 8'h28; 4'hf: result = 8'hdf;
                endcase
            end
            4'hf: begin
                case (value[3:0])
                    4'h0: result = 8'h8c; 4'h1: result = 8'ha1;
                    4'h2: result = 8'h89; 4'h3: result = 8'h0d;
                    4'h4: result = 8'hbf; 4'h5: result = 8'he6;
                    4'h6: result = 8'h42; 4'h7: result = 8'h68;
                    4'h8: result = 8'h41; 4'h9: result = 8'h99;
                    4'ha: result = 8'h2d; 4'hb: result = 8'h0f;
                    4'hc: result = 8'hb0; 4'hd: result = 8'h54;
                    4'he: result = 8'hbb; 4'hf: result = 8'h16;
                endcase
            end
            default: result = 8'h00;
        endcase
    end
endmodule

`timescale 1ns/1ps
// @latency 0
module aes_round (
    input  wire [127:0] state_in,
    input  wire [127:0] round_key,
    input  wire         final_round,
    output wire [127:0] state_out
);

    wire [127:0] sub_state;
    reg [127:0] shifted_state;
    reg [127:0] mixed_state;
    integer row;
    integer col;
    genvar byte_index;

    generate
        for (byte_index = 0; byte_index < 16; byte_index = byte_index + 1) begin : gen_sbox
            aes_sbox_lookup u_sbox (
                .value(state_in[127 - 8*byte_index -: 8]),
                .result(sub_state[127 - 8*byte_index -: 8])
            );
        end
    endgenerate

    function [7:0] xtime;
        input [7:0] value;
        begin
            if (value[7])
                xtime = (value << 1) ^ 8'h1b;
            else
                xtime = value << 1;
        end
    endfunction

    function [31:0] mix_column;
        input [31:0] column_in;
        reg [7:0] a0;
        reg [7:0] a1;
        reg [7:0] a2;
        reg [7:0] a3;
        reg [7:0] t;
        begin
            a0 = column_in[31:24];
            a1 = column_in[23:16];
            a2 = column_in[15:8];
            a3 = column_in[7:0];

            t = a0 ^ a1 ^ a2 ^ a3;
            mix_column[31:24] = a0 ^ t ^ xtime(a0 ^ a1);
            mix_column[23:16] = a1 ^ t ^ xtime(a1 ^ a2);
            mix_column[15:8]  = a2 ^ t ^ xtime(a2 ^ a3);
            mix_column[7:0]   = a3 ^ t ^ xtime(a3 ^ a0);
        end
    endfunction

    always @(*) begin
        shifted_state = 128'b0;
        mixed_state = 128'b0;

        for (row = 0; row < 4; row = row + 1) begin
            for (col = 0; col < 4; col = col + 1) begin
                shifted_state[127 - 8*(row + 4*col) -: 8] =
                    sub_state[127 - 8*(row + 4*((col + row) % 4)) -: 8];
            end
        end

        mixed_state = shifted_state;
        if (!final_round) begin
            for (col = 0; col < 4; col = col + 1) begin
                mixed_state[127 - 32*col -: 32] =
                    mix_column(shifted_state[127 - 32*col -: 32]);
            end
        end
    end

    assign state_out = mixed_state ^ round_key;

endmodule

`timescale 1ns/1ps
// @latency 0
module aes_key_step (
    input  wire [127:0] key_in,
    input  wire [7:0]   rcon,
    output wire [127:0] key_out
);

    wire [31:0] w0;
    wire [31:0] w1;
    wire [31:0] w2;
    wire [31:0] w3;
    wire [31:0] temp;
    wire [31:0] w4;
    wire [31:0] w5;
    wire [31:0] w6;
    wire [31:0] w7;
    wire [7:0] sb0;
    wire [7:0] sb1;
    wire [7:0] sb2;
    wire [7:0] sb3;

    assign w0 = key_in[127:96];
    assign w1 = key_in[95:64];
    assign w2 = key_in[63:32];
    assign w3 = key_in[31:0];

    aes_sbox_lookup u_sbox0 (.value(w3[23:16]), .result(sb0));
    aes_sbox_lookup u_sbox1 (.value(w3[15:8]),  .result(sb1));
    aes_sbox_lookup u_sbox2 (.value(w3[7:0]),   .result(sb2));
    aes_sbox_lookup u_sbox3 (.value(w3[31:24]), .result(sb3));

    assign temp = {sb0, sb1, sb2, sb3} ^ {rcon, 24'b0};

    assign w4 = w0 ^ temp;
    assign w5 = w1 ^ w4;
    assign w6 = w2 ^ w5;
    assign w7 = w3 ^ w6;

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