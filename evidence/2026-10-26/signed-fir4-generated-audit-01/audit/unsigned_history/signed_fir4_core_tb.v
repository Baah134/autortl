`timescale 1ns/1ps
module signed_fir4_core_tb;
reg _autortl_clk = 0;
always #5 _autortl_clk = ~_autortl_clk;
reg rst;
reg signed [7:0] x;
reg in_valid;
wire in_ready;
wire signed [12:0] out_data;
wire out_valid;
reg out_ready;
integer _autortl_cycle, _autortl_errors, _autortl_index;
integer _autortl_push, _autortl_pop, _autortl_drain;
reg _autortl_stalled;
integer _autortl_accepted_cycle [0:103];
reg signed [12:0] _autortl_held_out_data;
reg signed [7:0] _autortl_stim_x [0:103];
reg signed [12:0] _autortl_exp_out_data [0:103];
signed_fir4_core dut (.clk(_autortl_clk), .rst(rst), .x(x), .in_valid(in_valid), .in_ready(in_ready), .out_data(out_data), .out_valid(out_valid), .out_ready(out_ready));
initial begin
_autortl_errors = 0;
rst = 0;
x = 0;
in_valid = 0;
out_ready = 0;
_autortl_stim_x[0] = 8'd0;
_autortl_stim_x[1] = 8'd255;
_autortl_stim_x[2] = 8'd128;
_autortl_stim_x[3] = 8'd127;
_autortl_stim_x[4] = 8'd225;
_autortl_stim_x[5] = 8'd59;
_autortl_stim_x[6] = 8'd3;
_autortl_stim_x[7] = 8'd46;
_autortl_stim_x[8] = 8'd17;
_autortl_stim_x[9] = 8'd42;
_autortl_stim_x[10] = 8'd50;
_autortl_stim_x[11] = 8'd181;
_autortl_stim_x[12] = 8'd121;
_autortl_stim_x[13] = 8'd8;
_autortl_stim_x[14] = 8'd15;
_autortl_stim_x[15] = 8'd8;
_autortl_stim_x[16] = 8'd177;
_autortl_stim_x[17] = 8'd247;
_autortl_stim_x[18] = 8'd237;
_autortl_stim_x[19] = 8'd76;
_autortl_stim_x[20] = 8'd46;
_autortl_stim_x[21] = 8'd93;
_autortl_stim_x[22] = 8'd58;
_autortl_stim_x[23] = 8'd7;
_autortl_stim_x[24] = 8'd249;
_autortl_stim_x[25] = 8'd127;
_autortl_stim_x[26] = 8'd33;
_autortl_stim_x[27] = 8'd238;
_autortl_stim_x[28] = 8'd35;
_autortl_stim_x[29] = 8'd45;
_autortl_stim_x[30] = 8'd23;
_autortl_stim_x[31] = 8'd138;
_autortl_stim_x[32] = 8'd32;
_autortl_stim_x[33] = 8'd154;
_autortl_stim_x[34] = 8'd246;
_autortl_stim_x[35] = 8'd181;
_autortl_stim_x[36] = 8'd136;
_autortl_stim_x[37] = 8'd127;
_autortl_stim_x[38] = 8'd102;
_autortl_stim_x[39] = 8'd232;
_autortl_stim_x[40] = 8'd9;
_autortl_stim_x[41] = 8'd36;
_autortl_stim_x[42] = 8'd2;
_autortl_stim_x[43] = 8'd170;
_autortl_stim_x[44] = 8'd73;
_autortl_stim_x[45] = 8'd242;
_autortl_stim_x[46] = 8'd193;
_autortl_stim_x[47] = 8'd85;
_autortl_stim_x[48] = 8'd27;
_autortl_stim_x[49] = 8'd39;
_autortl_stim_x[50] = 8'd254;
_autortl_stim_x[51] = 8'd83;
_autortl_stim_x[52] = 8'd38;
_autortl_stim_x[53] = 8'd110;
_autortl_stim_x[54] = 8'd73;
_autortl_stim_x[55] = 8'd13;
_autortl_stim_x[56] = 8'd177;
_autortl_stim_x[57] = 8'd56;
_autortl_stim_x[58] = 8'd72;
_autortl_stim_x[59] = 8'd156;
_autortl_stim_x[60] = 8'd232;
_autortl_stim_x[61] = 8'd20;
_autortl_stim_x[62] = 8'd213;
_autortl_stim_x[63] = 8'd141;
_autortl_stim_x[64] = 8'd20;
_autortl_stim_x[65] = 8'd90;
_autortl_stim_x[66] = 8'd139;
_autortl_stim_x[67] = 8'd79;
_autortl_stim_x[68] = 8'd153;
_autortl_stim_x[69] = 8'd79;
_autortl_stim_x[70] = 8'd237;
_autortl_stim_x[71] = 8'd21;
_autortl_stim_x[72] = 8'd197;
_autortl_stim_x[73] = 8'd178;
_autortl_stim_x[74] = 8'd253;
_autortl_stim_x[75] = 8'd174;
_autortl_stim_x[76] = 8'd239;
_autortl_stim_x[77] = 8'd243;
_autortl_stim_x[78] = 8'd23;
_autortl_stim_x[79] = 8'd241;
_autortl_stim_x[80] = 8'd87;
_autortl_stim_x[81] = 8'd225;
_autortl_stim_x[82] = 8'd224;
_autortl_stim_x[83] = 8'd151;
_autortl_stim_x[84] = 8'd140;
_autortl_stim_x[85] = 8'd63;
_autortl_stim_x[86] = 8'd95;
_autortl_stim_x[87] = 8'd213;
_autortl_stim_x[88] = 8'd223;
_autortl_stim_x[89] = 8'd61;
_autortl_stim_x[90] = 8'd52;
_autortl_stim_x[91] = 8'd248;
_autortl_stim_x[92] = 8'd192;
_autortl_stim_x[93] = 8'd130;
_autortl_stim_x[94] = 8'd98;
_autortl_stim_x[95] = 8'd176;
_autortl_stim_x[96] = 8'd55;
_autortl_stim_x[97] = 8'd80;
_autortl_stim_x[98] = 8'd137;
_autortl_stim_x[99] = 8'd79;
_autortl_stim_x[100] = 8'd165;
_autortl_stim_x[101] = 8'd228;
_autortl_stim_x[102] = 8'd36;
_autortl_stim_x[103] = 8'd40;
_autortl_exp_out_data[0] = 13'd0;
_autortl_exp_out_data[1] = 13'd8189;
_autortl_exp_out_data[2] = 13'd7813;
_autortl_exp_out_data[3] = 13'd1014;
_autortl_exp_out_data[4] = 13'd6570;
_autortl_exp_out_data[5] = 13'd1477;
_autortl_exp_out_data[6] = 13'd7435;
_autortl_exp_out_data[7] = 13'd598;
_autortl_exp_out_data[8] = 13'd7916;
_autortl_exp_out_data[9] = 13'd357;
_autortl_exp_out_data[10] = 13'd8159;
_autortl_exp_out_data[11] = 13'd7977;
_autortl_exp_out_data[12] = 13'd1004;
_autortl_exp_out_data[13] = 13'd6986;
_autortl_exp_out_data[14] = 13'd1002;
_autortl_exp_out_data[15] = 13'd7955;
_autortl_exp_out_data[16] = 13'd8004;
_autortl_exp_out_data[17] = 13'd394;
_autortl_exp_out_data[18] = 13'd7611;
_autortl_exp_out_data[19] = 13'd418;
_autortl_exp_out_data[20] = 13'd7835;
_autortl_exp_out_data[21] = 13'd619;
_autortl_exp_out_data[22] = 13'd8071;
_autortl_exp_out_data[23] = 13'd290;
_autortl_exp_out_data[24] = 13'd164;
_autortl_exp_out_data[25] = 13'd349;
_autortl_exp_out_data[26] = 13'd7593;
_autortl_exp_out_data[27] = 13'd684;
_autortl_exp_out_data[28] = 13'd172;
_autortl_exp_out_data[29] = 13'd7960;
_autortl_exp_out_data[30] = 13'd125;
_autortl_exp_out_data[31] = 13'd7968;
_autortl_exp_out_data[32] = 13'd757;
_autortl_exp_out_data[33] = 13'd6854;
_autortl_exp_out_data[34] = 13'd940;
_autortl_exp_out_data[35] = 13'd7239;
_autortl_exp_out_data[36] = 13'd149;
_autortl_exp_out_data[37] = 13'd476;
_autortl_exp_out_data[38] = 13'd7173;
_autortl_exp_out_data[39] = 13'd547;
_autortl_exp_out_data[40] = 13'd607;
_autortl_exp_out_data[41] = 13'd7883;
_autortl_exp_out_data[42] = 13'd8129;
_autortl_exp_out_data[43] = 13'd8158;
_autortl_exp_out_data[44] = 13'd591;
_autortl_exp_out_data[45] = 13'd7179;
_autortl_exp_out_data[46] = 13'd564;
_autortl_exp_out_data[47] = 13'd326;
_autortl_exp_out_data[48] = 13'd7435;
_autortl_exp_out_data[49] = 13'd703;
_autortl_exp_out_data[50] = 13'd8010;
_autortl_exp_out_data[51] = 13'd478;
_autortl_exp_out_data[52] = 13'd7799;
_autortl_exp_out_data[53] = 13'd725;
_autortl_exp_out_data[54] = 13'd7961;
_autortl_exp_out_data[55] = 13'd368;
_autortl_exp_out_data[56] = 13'd8181;
_autortl_exp_out_data[57] = 13'd508;
_autortl_exp_out_data[58] = 13'd7549;
_autortl_exp_out_data[59] = 13'd8082;
_autortl_exp_out_data[60] = 13'd820;
_autortl_exp_out_data[61] = 13'd7528;
_autortl_exp_out_data[62] = 13'd7995;
_autortl_exp_out_data[63] = 13'd58;
_autortl_exp_out_data[64] = 13'd294;
_autortl_exp_out_data[65] = 13'd7643;
_autortl_exp_out_data[66] = 13'd7761;
_autortl_exp_out_data[67] = 13'd1412;
_autortl_exp_out_data[68] = 13'd6489;
_autortl_exp_out_data[69] = 13'd1539;
_autortl_exp_out_data[70] = 13'd6861;
_autortl_exp_out_data[71] = 13'd917;
_autortl_exp_out_data[72] = 13'd7619;
_autortl_exp_out_data[73] = 13'd246;
_autortl_exp_out_data[74] = 13'd8118;
_autortl_exp_out_data[75] = 13'd7533;
_autortl_exp_out_data[76] = 13'd494;
_autortl_exp_out_data[77] = 13'd7670;
_autortl_exp_out_data[78] = 13'd179;
_autortl_exp_out_data[79] = 13'd7975;
_autortl_exp_out_data[80] = 13'd523;
_autortl_exp_out_data[81] = 13'd7513;
_autortl_exp_out_data[82] = 13'd698;
_autortl_exp_out_data[83] = 13'd7646;
_autortl_exp_out_data[84] = 13'd15;
_autortl_exp_out_data[85] = 13'd98;
_autortl_exp_out_data[86] = 13'd7560;
_autortl_exp_out_data[87] = 13'd69;
_autortl_exp_out_data[88] = 13'd655;
_autortl_exp_out_data[89] = 13'd8049;
_autortl_exp_out_data[90] = 13'd7898;
_autortl_exp_out_data[91] = 13'd209;
_autortl_exp_out_data[92] = 13'd90;
_autortl_exp_out_data[93] = 13'd7974;
_autortl_exp_out_data[94] = 13'd492;
_autortl_exp_out_data[95] = 13'd6708;
_autortl_exp_out_data[96] = 13'd1503;
_autortl_exp_out_data[97] = 13'd7401;
_autortl_exp_out_data[98] = 13'd7980;
_autortl_exp_out_data[99] = 13'd1282;
_autortl_exp_out_data[100] = 13'd6531;
_autortl_exp_out_data[101] = 13'd1162;
_autortl_exp_out_data[102] = 13'd7645;
_autortl_exp_out_data[103] = 13'd8118;
rst = 1'b1;
repeat (3) @(posedge _autortl_clk);
@(negedge _autortl_clk);
rst = 1'b0;
_autortl_push=0; _autortl_pop=0; _autortl_drain=0; _autortl_stalled=0;
for (_autortl_cycle=0; _autortl_cycle<1592 && _autortl_drain<4; _autortl_cycle=_autortl_cycle+1) begin
if (_autortl_cycle > 0) @(negedge _autortl_clk);
in_valid = (_autortl_push < 104);
out_ready = (_autortl_cycle % 7 >= 2); // periodic backpressure
if (_autortl_push < 104) begin
x = _autortl_stim_x[_autortl_push];
end
@(posedge _autortl_clk); // sample accepted transfers BEFORE NBA
if ((in_ready !== 1'b0 && in_ready !== 1'b1) || (out_valid !== 1'b0 && out_valid !== 1'b1)) begin
$display("FAIL unknown handshake"); _autortl_errors=_autortl_errors+1; end
if (_autortl_stalled) begin
if (out_valid !== 1'b1) begin $display("FAIL valid dropped under backpressure"); _autortl_errors=_autortl_errors+1; end
if (out_data !== _autortl_held_out_data) begin $display("FAIL unstable out_data"); _autortl_errors=_autortl_errors+1; end
end
if (in_valid === 1'b1 && in_ready === 1'b1) begin
_autortl_accepted_cycle[_autortl_push]=_autortl_cycle;
_autortl_push=_autortl_push+1; end
if (out_valid === 1'b1 && out_ready === 1'b1) begin
if (_autortl_pop >= _autortl_push || _autortl_pop >= 104) begin
$display("FAIL unexpected output transaction"); _autortl_errors=_autortl_errors+1;
end else begin
if (_autortl_cycle - _autortl_accepted_cycle[_autortl_pop] < 3) begin
$display("FAIL output before minimum transfer latency"); _autortl_errors=_autortl_errors+1; end
if (out_data !== _autortl_exp_out_data[_autortl_pop]) begin $display("FAIL index=%0d signal=out_data", _autortl_pop); _autortl_errors = _autortl_errors + 1; end
end
_autortl_pop=_autortl_pop+1;
end
_autortl_stalled=(out_valid === 1'b1 && out_ready === 1'b0);
_autortl_held_out_data=out_data;
if (_autortl_pop >= 104) _autortl_drain=_autortl_drain+1;
end
if (_autortl_push != 104 || _autortl_pop != 104) begin
$display("FAIL scoreboard did not drain"); _autortl_errors=_autortl_errors+1; end
if (_autortl_errors == 0) $display("TEST PASSED");
else $display("TEST FAILED: %0d errors", _autortl_errors);
$finish;
end
initial begin #16150; $display("TEST FAILED: watchdog timeout"); $finish; end
endmodule
