`timescale 1ns/1ps
module fir16_sym_core_tb;
reg _autortl_clk = 0;
always #5 _autortl_clk = ~_autortl_clk;
reg rst;
reg signed [15:0] in_sample;
reg in_valid;
wire in_ready;
wire signed [15:0] out_sample;
wire out_valid;
reg out_ready;
integer _autortl_cycle, _autortl_errors, _autortl_index;
integer _autortl_push, _autortl_pop, _autortl_drain;
reg _autortl_stalled;
reg _autortl_input_stalled, _autortl_noise;
integer _autortl_accepted_cycle [0:110];
reg signed [15:0] _autortl_held_out_sample;
reg signed [15:0] _autortl_stim_in_sample [0:110];
reg signed [15:0] _autortl_exp_out_sample [0:110];
fir16_sym_core dut (.clk(_autortl_clk), .rst(rst), .in_sample(in_sample), .in_valid(in_valid), .in_ready(in_ready), .out_sample(out_sample), .out_valid(out_valid), .out_ready(out_ready));
initial begin
_autortl_errors = 0;
rst = 0;
in_sample = 0;
in_valid = 0;
out_ready = 0;
_autortl_stim_in_sample[0] = 16'd0;
_autortl_stim_in_sample[1] = 16'd65535;
_autortl_stim_in_sample[2] = 16'd32768;
_autortl_stim_in_sample[3] = 16'd1000;
_autortl_stim_in_sample[4] = 16'd32767;
_autortl_stim_in_sample[5] = 16'd32768;
_autortl_stim_in_sample[6] = 16'd32767;
_autortl_stim_in_sample[7] = 16'd32768;
_autortl_stim_in_sample[8] = 16'd32767;
_autortl_stim_in_sample[9] = 16'd32768;
_autortl_stim_in_sample[10] = 16'd32767;
_autortl_stim_in_sample[11] = 16'd57767;
_autortl_stim_in_sample[12] = 16'd15315;
_autortl_stim_in_sample[13] = 16'd981;
_autortl_stim_in_sample[14] = 16'd11880;
_autortl_stim_in_sample[15] = 16'd4577;
_autortl_stim_in_sample[16] = 16'd11001;
_autortl_stim_in_sample[17] = 16'd12900;
_autortl_stim_in_sample[18] = 16'd46482;
_autortl_stim_in_sample[19] = 16'd31039;
_autortl_stim_in_sample[20] = 16'd2284;
_autortl_stim_in_sample[21] = 16'd4038;
_autortl_stim_in_sample[22] = 16'd2076;
_autortl_stim_in_sample[23] = 16'd45362;
_autortl_stim_in_sample[24] = 16'd63471;
_autortl_stim_in_sample[25] = 16'd60758;
_autortl_stim_in_sample[26] = 16'd19471;
_autortl_stim_in_sample[27] = 16'd11965;
_autortl_stim_in_sample[28] = 16'd23998;
_autortl_stim_in_sample[29] = 16'd14996;
_autortl_stim_in_sample[30] = 16'd1916;
_autortl_stim_in_sample[31] = 16'd63799;
_autortl_stim_in_sample[32] = 16'd32745;
_autortl_stim_in_sample[33] = 16'd8462;
_autortl_stim_in_sample[34] = 16'd61066;
_autortl_stim_in_sample[35] = 16'd8987;
_autortl_stim_in_sample[36] = 16'd11656;
_autortl_stim_in_sample[37] = 16'd6024;
_autortl_stim_in_sample[38] = 16'd35335;
_autortl_stim_in_sample[39] = 16'd8267;
_autortl_stim_in_sample[40] = 16'd39639;
_autortl_stim_in_sample[41] = 16'd63050;
_autortl_stim_in_sample[42] = 16'd46561;
_autortl_stim_in_sample[43] = 16'd34924;
_autortl_stim_in_sample[44] = 16'd32656;
_autortl_stim_in_sample[45] = 16'd26218;
_autortl_stim_in_sample[46] = 16'd59426;
_autortl_stim_in_sample[47] = 16'd2529;
_autortl_stim_in_sample[48] = 16'd9252;
_autortl_stim_in_sample[49] = 16'd757;
_autortl_stim_in_sample[50] = 16'd43713;
_autortl_stim_in_sample[51] = 16'd18844;
_autortl_stim_in_sample[52] = 16'd61974;
_autortl_stim_in_sample[53] = 16'd49459;
_autortl_stim_in_sample[54] = 16'd21903;
_autortl_stim_in_sample[55] = 16'd7100;
_autortl_stim_in_sample[56] = 16'd9992;
_autortl_stim_in_sample[57] = 16'd65087;
_autortl_stim_in_sample[58] = 16'd21496;
_autortl_stim_in_sample[59] = 16'd9872;
_autortl_stim_in_sample[60] = 16'd28192;
_autortl_stim_in_sample[61] = 16'd18906;
_autortl_stim_in_sample[62] = 16'd3555;
_autortl_stim_in_sample[63] = 16'd45381;
_autortl_stim_in_sample[64] = 16'd14534;
_autortl_stim_in_sample[65] = 16'd18511;
_autortl_stim_in_sample[66] = 16'd40028;
_autortl_stim_in_sample[67] = 16'd59525;
_autortl_stim_in_sample[68] = 16'd5189;
_autortl_stim_in_sample[69] = 16'd54558;
_autortl_stim_in_sample[70] = 16'd36278;
_autortl_stim_in_sample[71] = 16'd5269;
_autortl_stim_in_sample[72] = 16'd23244;
_autortl_stim_in_sample[73] = 16'd35608;
_autortl_stim_in_sample[74] = 16'd20259;
_autortl_stim_in_sample[75] = 16'd39357;
_autortl_stim_in_sample[76] = 16'd20257;
_autortl_stim_in_sample[77] = 16'd60883;
_autortl_stim_in_sample[78] = 16'd5382;
_autortl_stim_in_sample[79] = 16'd50617;
_autortl_stim_in_sample[80] = 16'd45821;
_autortl_stim_in_sample[81] = 16'd64992;
_autortl_stim_in_sample[82] = 16'd44788;
_autortl_stim_in_sample[83] = 16'd61357;
_autortl_stim_in_sample[84] = 16'd62381;
_autortl_stim_in_sample[85] = 16'd5941;
_autortl_stim_in_sample[86] = 16'd61713;
_autortl_stim_in_sample[87] = 16'd22278;
_autortl_stim_in_sample[88] = 16'd57618;
_autortl_stim_in_sample[89] = 16'd57392;
_autortl_stim_in_sample[90] = 16'd38755;
_autortl_stim_in_sample[91] = 16'd36050;
_autortl_stim_in_sample[92] = 16'd16236;
_autortl_stim_in_sample[93] = 16'd24329;
_autortl_stim_in_sample[94] = 16'd54568;
_autortl_stim_in_sample[95] = 16'd57155;
_autortl_stim_in_sample[96] = 16'd15658;
_autortl_stim_in_sample[97] = 16'd13512;
_autortl_stim_in_sample[98] = 16'd63596;
_autortl_stim_in_sample[99] = 16'd49390;
_autortl_stim_in_sample[100] = 16'd33485;
_autortl_stim_in_sample[101] = 16'd25088;
_autortl_stim_in_sample[102] = 16'd45265;
_autortl_stim_in_sample[103] = 16'd14176;
_autortl_stim_in_sample[104] = 16'd20600;
_autortl_stim_in_sample[105] = 16'd35301;
_autortl_stim_in_sample[106] = 16'd20296;
_autortl_stim_in_sample[107] = 16'd42400;
_autortl_stim_in_sample[108] = 16'd58546;
_autortl_stim_in_sample[109] = 16'd9276;
_autortl_stim_in_sample[110] = 16'd10288;
_autortl_exp_out_sample[0] = 16'd0;
_autortl_exp_out_sample[1] = 16'd0;
_autortl_exp_out_sample[2] = 16'd96;
_autortl_exp_out_sample[3] = 16'd317;
_autortl_exp_out_sample[4] = 16'd278;
_autortl_exp_out_sample[5] = 16'd65012;
_autortl_exp_out_sample[6] = 16'd63625;
_autortl_exp_out_sample[7] = 16'd62422;
_autortl_exp_out_sample[8] = 16'd61678;
_autortl_exp_out_sample[9] = 16'd61761;
_autortl_exp_out_sample[10] = 16'd62462;
_autortl_exp_out_sample[11] = 16'd63637;
_autortl_exp_out_sample[12] = 16'd64864;
_autortl_exp_out_sample[13] = 16'd432;
_autortl_exp_out_sample[14] = 16'd1233;
_autortl_exp_out_sample[15] = 16'd1729;
_autortl_exp_out_sample[16] = 16'd2210;
_autortl_exp_out_sample[17] = 16'd3234;
_autortl_exp_out_sample[18] = 16'd4741;
_autortl_exp_out_sample[19] = 16'd6168;
_autortl_exp_out_sample[20] = 16'd7192;
_autortl_exp_out_sample[21] = 16'd7451;
_autortl_exp_out_sample[22] = 16'd7386;
_autortl_exp_out_sample[23] = 16'd7238;
_autortl_exp_out_sample[24] = 16'd7346;
_autortl_exp_out_sample[25] = 16'd7312;
_autortl_exp_out_sample[26] = 16'd6548;
_autortl_exp_out_sample[27] = 16'd4745;
_autortl_exp_out_sample[28] = 16'd2260;
_autortl_exp_out_sample[29] = 16'd65392;
_autortl_exp_out_sample[30] = 16'd64078;
_autortl_exp_out_sample[31] = 16'd64585;
_autortl_exp_out_sample[32] = 16'd1474;
_autortl_exp_out_sample[33] = 16'd5186;
_autortl_exp_out_sample[34] = 16'd8919;
_autortl_exp_out_sample[35] = 16'd11840;
_autortl_exp_out_sample[36] = 16'd13312;
_autortl_exp_out_sample[37] = 16'd13139;
_autortl_exp_out_sample[38] = 16'd11990;
_autortl_exp_out_sample[39] = 16'd10743;
_autortl_exp_out_sample[40] = 16'd9778;
_autortl_exp_out_sample[41] = 16'd8580;
_autortl_exp_out_sample[42] = 16'd6692;
_autortl_exp_out_sample[43] = 16'd3807;
_autortl_exp_out_sample[44] = 16'd80;
_autortl_exp_out_sample[45] = 16'd61401;
_autortl_exp_out_sample[46] = 16'd57289;
_autortl_exp_out_sample[47] = 16'd54449;
_autortl_exp_out_sample[48] = 16'd54039;
_autortl_exp_out_sample[49] = 16'd56311;
_autortl_exp_out_sample[50] = 16'd60600;
_autortl_exp_out_sample[51] = 16'd65453;
_autortl_exp_out_sample[52] = 16'd3884;
_autortl_exp_out_sample[53] = 16'd6122;
_autortl_exp_out_sample[54] = 16'd6296;
_autortl_exp_out_sample[55] = 16'd4608;
_autortl_exp_out_sample[56] = 16'd1761;
_autortl_exp_out_sample[57] = 16'd64961;
_autortl_exp_out_sample[58] = 16'd64372;
_autortl_exp_out_sample[59] = 16'd65314;
_autortl_exp_out_sample[60] = 16'd1378;
_autortl_exp_out_sample[61] = 16'd3299;
_autortl_exp_out_sample[62] = 16'd5530;
_autortl_exp_out_sample[63] = 16'd8086;
_autortl_exp_out_sample[64] = 16'd10820;
_autortl_exp_out_sample[65] = 16'd13147;
_autortl_exp_out_sample[66] = 16'd14112;
_autortl_exp_out_sample[67] = 16'd13706;
_autortl_exp_out_sample[68] = 16'd12380;
_autortl_exp_out_sample[69] = 16'd9988;
_autortl_exp_out_sample[70] = 16'd6696;
_autortl_exp_out_sample[71] = 16'd3202;
_autortl_exp_out_sample[72] = 16'd8;
_autortl_exp_out_sample[73] = 16'd62745;
_autortl_exp_out_sample[74] = 16'd60603;
_autortl_exp_out_sample[75] = 16'd59326;
_autortl_exp_out_sample[76] = 16'd58730;
_autortl_exp_out_sample[77] = 16'd58963;
_autortl_exp_out_sample[78] = 16'd60018;
_autortl_exp_out_sample[79] = 16'd61572;
_autortl_exp_out_sample[80] = 16'd63168;
_autortl_exp_out_sample[81] = 16'd64610;
_autortl_exp_out_sample[82] = 16'd65478;
_autortl_exp_out_sample[83] = 16'd65191;
_autortl_exp_out_sample[84] = 16'd63828;
_autortl_exp_out_sample[85] = 16'd61908;
_autortl_exp_out_sample[86] = 16'd59688;
_autortl_exp_out_sample[87] = 16'd57412;
_autortl_exp_out_sample[88] = 16'd55922;
_autortl_exp_out_sample[89] = 16'd55969;
_autortl_exp_out_sample[90] = 16'd58094;
_autortl_exp_out_sample[91] = 16'd61575;
_autortl_exp_out_sample[92] = 16'd64937;
_autortl_exp_out_sample[93] = 16'd834;
_autortl_exp_out_sample[94] = 16'd65227;
_autortl_exp_out_sample[95] = 16'd62548;
_autortl_exp_out_sample[96] = 16'd59871;
_autortl_exp_out_sample[97] = 16'd58210;
_autortl_exp_out_sample[98] = 16'd58100;
_autortl_exp_out_sample[99] = 16'd59871;
_autortl_exp_out_sample[100] = 16'd63348;
_autortl_exp_out_sample[101] = 16'd1798;
_autortl_exp_out_sample[102] = 16'd4274;
_autortl_exp_out_sample[103] = 16'd4009;
_autortl_exp_out_sample[104] = 16'd1518;
_autortl_exp_out_sample[105] = 16'd63891;
_autortl_exp_out_sample[106] = 16'd61727;
_autortl_exp_out_sample[107] = 16'd61119;
_autortl_exp_out_sample[108] = 16'd61539;
_autortl_exp_out_sample[109] = 16'd62876;
_autortl_exp_out_sample[110] = 16'd64541;
rst = 1'b1;
repeat (3) @(posedge _autortl_clk);
@(negedge _autortl_clk);
rst = 1'b0;
_autortl_push=0; _autortl_pop=0; _autortl_drain=0; _autortl_stalled=0; _autortl_input_stalled=0; _autortl_noise=0;
for (_autortl_cycle=0; _autortl_cycle<1919 && _autortl_drain<4; _autortl_cycle=_autortl_cycle+1) begin
if (_autortl_cycle > 0) @(negedge _autortl_clk);
out_ready = (_autortl_cycle % 7 >= 2); // periodic backpressure
if (!_autortl_input_stalled) begin
in_valid = (_autortl_push < 111 && _autortl_cycle % 5 != 0);
if (in_valid) begin
in_sample = _autortl_stim_in_sample[_autortl_push];
end else begin
_autortl_noise = !_autortl_noise;
in_sample = _autortl_noise ? 16'd65535 : 16'd0;
end
end
if (_autortl_push > 0 && (_autortl_push < 111 || _autortl_pop < _autortl_push) && _autortl_cycle % 11 == 5) begin
// complete off-edge pulse; all other inputs stay held
#1; rst = 1'b1;
#2; rst = 1'b0;
end
@(posedge _autortl_clk); // sample accepted transfers BEFORE NBA
if ((in_ready !== 1'b0 && in_ready !== 1'b1) || (out_valid !== 1'b0 && out_valid !== 1'b1)) begin
$display("FAIL unknown handshake"); _autortl_errors=_autortl_errors+1; end
_autortl_input_stalled=(in_valid === 1'b1 && in_ready === 1'b0);
if (_autortl_stalled) begin
if (out_valid !== 1'b1) begin $display("FAIL valid dropped under backpressure"); _autortl_errors=_autortl_errors+1; end
if (out_sample !== _autortl_held_out_sample) begin $display("FAIL unstable out_sample"); _autortl_errors=_autortl_errors+1; end
end
if (in_valid === 1'b1 && in_ready === 1'b1) begin
_autortl_accepted_cycle[_autortl_push]=_autortl_cycle;
_autortl_push=_autortl_push+1; end
if (out_valid === 1'b1 && out_ready === 1'b1) begin
if (_autortl_pop >= _autortl_push || _autortl_pop >= 111) begin
$display("FAIL unexpected output transaction"); _autortl_errors=_autortl_errors+1;
end else begin
if (_autortl_cycle - _autortl_accepted_cycle[_autortl_pop] < 5) begin
$display("FAIL output before minimum transfer latency"); _autortl_errors=_autortl_errors+1; end
if (out_sample !== _autortl_exp_out_sample[_autortl_pop]) begin $display("FAIL index=%0d signal=out_sample", _autortl_pop); _autortl_errors = _autortl_errors + 1; end
end
_autortl_pop=_autortl_pop+1;
end
_autortl_stalled=(out_valid === 1'b1 && out_ready === 1'b0);
_autortl_held_out_sample=out_sample;
if (_autortl_pop >= 111) _autortl_drain=_autortl_drain+1;
end
if (_autortl_push != 111 || _autortl_pop != 111) begin
$display("FAIL scoreboard did not drain"); _autortl_errors=_autortl_errors+1; end
if (_autortl_errors == 0) $display("TEST PASSED");
else $display("TEST FAILED: %0d errors", _autortl_errors);
$finish;
end
initial begin #19420; $display("TEST FAILED: watchdog timeout"); $finish; end
endmodule
