`timescale 1ns/1ps
module sync_fifo_core_tb;
reg _autortl_clk = 0;
always #5 _autortl_clk = ~_autortl_clk;
reg rst;
reg [7:0] in_data;
reg in_valid;
wire in_ready;
wire [7:0] out_data;
wire out_valid;
reg out_ready;
integer _autortl_cycle, _autortl_errors, _autortl_index;
integer _autortl_push, _autortl_pop, _autortl_drain;
reg _autortl_stalled;
reg _autortl_input_stalled, _autortl_noise;
integer _autortl_accepted_cycle [0:103];
reg [7:0] _autortl_held_out_data;
reg [7:0] _autortl_stim_in_data [0:103];
reg [7:0] _autortl_exp_out_data [0:103];
sync_fifo_core #( .WIDTH(8), .DEPTH(3) ) dut (.clk(_autortl_clk), .rst(rst), .in_data(in_data), .in_valid(in_valid), .in_ready(in_ready), .out_data(out_data), .out_valid(out_valid), .out_ready(out_ready));
initial begin
_autortl_errors = 0;
rst = 0;
in_data = 0;
in_valid = 0;
out_ready = 0;
_autortl_stim_in_data[0] = 8'd0;
_autortl_stim_in_data[1] = 8'd255;
_autortl_stim_in_data[2] = 8'd128;
_autortl_stim_in_data[3] = 8'd165;
_autortl_stim_in_data[4] = 8'd225;
_autortl_stim_in_data[5] = 8'd59;
_autortl_stim_in_data[6] = 8'd3;
_autortl_stim_in_data[7] = 8'd46;
_autortl_stim_in_data[8] = 8'd17;
_autortl_stim_in_data[9] = 8'd42;
_autortl_stim_in_data[10] = 8'd50;
_autortl_stim_in_data[11] = 8'd181;
_autortl_stim_in_data[12] = 8'd121;
_autortl_stim_in_data[13] = 8'd8;
_autortl_stim_in_data[14] = 8'd15;
_autortl_stim_in_data[15] = 8'd8;
_autortl_stim_in_data[16] = 8'd177;
_autortl_stim_in_data[17] = 8'd247;
_autortl_stim_in_data[18] = 8'd237;
_autortl_stim_in_data[19] = 8'd76;
_autortl_stim_in_data[20] = 8'd46;
_autortl_stim_in_data[21] = 8'd93;
_autortl_stim_in_data[22] = 8'd58;
_autortl_stim_in_data[23] = 8'd7;
_autortl_stim_in_data[24] = 8'd249;
_autortl_stim_in_data[25] = 8'd127;
_autortl_stim_in_data[26] = 8'd33;
_autortl_stim_in_data[27] = 8'd238;
_autortl_stim_in_data[28] = 8'd35;
_autortl_stim_in_data[29] = 8'd45;
_autortl_stim_in_data[30] = 8'd23;
_autortl_stim_in_data[31] = 8'd138;
_autortl_stim_in_data[32] = 8'd32;
_autortl_stim_in_data[33] = 8'd154;
_autortl_stim_in_data[34] = 8'd246;
_autortl_stim_in_data[35] = 8'd181;
_autortl_stim_in_data[36] = 8'd136;
_autortl_stim_in_data[37] = 8'd127;
_autortl_stim_in_data[38] = 8'd102;
_autortl_stim_in_data[39] = 8'd232;
_autortl_stim_in_data[40] = 8'd9;
_autortl_stim_in_data[41] = 8'd36;
_autortl_stim_in_data[42] = 8'd2;
_autortl_stim_in_data[43] = 8'd170;
_autortl_stim_in_data[44] = 8'd73;
_autortl_stim_in_data[45] = 8'd242;
_autortl_stim_in_data[46] = 8'd193;
_autortl_stim_in_data[47] = 8'd85;
_autortl_stim_in_data[48] = 8'd27;
_autortl_stim_in_data[49] = 8'd39;
_autortl_stim_in_data[50] = 8'd254;
_autortl_stim_in_data[51] = 8'd83;
_autortl_stim_in_data[52] = 8'd38;
_autortl_stim_in_data[53] = 8'd110;
_autortl_stim_in_data[54] = 8'd73;
_autortl_stim_in_data[55] = 8'd13;
_autortl_stim_in_data[56] = 8'd177;
_autortl_stim_in_data[57] = 8'd56;
_autortl_stim_in_data[58] = 8'd72;
_autortl_stim_in_data[59] = 8'd156;
_autortl_stim_in_data[60] = 8'd232;
_autortl_stim_in_data[61] = 8'd20;
_autortl_stim_in_data[62] = 8'd213;
_autortl_stim_in_data[63] = 8'd141;
_autortl_stim_in_data[64] = 8'd20;
_autortl_stim_in_data[65] = 8'd90;
_autortl_stim_in_data[66] = 8'd139;
_autortl_stim_in_data[67] = 8'd79;
_autortl_stim_in_data[68] = 8'd153;
_autortl_stim_in_data[69] = 8'd79;
_autortl_stim_in_data[70] = 8'd237;
_autortl_stim_in_data[71] = 8'd21;
_autortl_stim_in_data[72] = 8'd197;
_autortl_stim_in_data[73] = 8'd178;
_autortl_stim_in_data[74] = 8'd253;
_autortl_stim_in_data[75] = 8'd174;
_autortl_stim_in_data[76] = 8'd239;
_autortl_stim_in_data[77] = 8'd243;
_autortl_stim_in_data[78] = 8'd23;
_autortl_stim_in_data[79] = 8'd241;
_autortl_stim_in_data[80] = 8'd87;
_autortl_stim_in_data[81] = 8'd225;
_autortl_stim_in_data[82] = 8'd224;
_autortl_stim_in_data[83] = 8'd151;
_autortl_stim_in_data[84] = 8'd140;
_autortl_stim_in_data[85] = 8'd63;
_autortl_stim_in_data[86] = 8'd95;
_autortl_stim_in_data[87] = 8'd213;
_autortl_stim_in_data[88] = 8'd223;
_autortl_stim_in_data[89] = 8'd61;
_autortl_stim_in_data[90] = 8'd52;
_autortl_stim_in_data[91] = 8'd248;
_autortl_stim_in_data[92] = 8'd192;
_autortl_stim_in_data[93] = 8'd130;
_autortl_stim_in_data[94] = 8'd98;
_autortl_stim_in_data[95] = 8'd176;
_autortl_stim_in_data[96] = 8'd55;
_autortl_stim_in_data[97] = 8'd80;
_autortl_stim_in_data[98] = 8'd137;
_autortl_stim_in_data[99] = 8'd79;
_autortl_stim_in_data[100] = 8'd165;
_autortl_stim_in_data[101] = 8'd228;
_autortl_stim_in_data[102] = 8'd36;
_autortl_stim_in_data[103] = 8'd40;
_autortl_exp_out_data[0] = 8'd0;
_autortl_exp_out_data[1] = 8'd255;
_autortl_exp_out_data[2] = 8'd128;
_autortl_exp_out_data[3] = 8'd165;
_autortl_exp_out_data[4] = 8'd225;
_autortl_exp_out_data[5] = 8'd59;
_autortl_exp_out_data[6] = 8'd3;
_autortl_exp_out_data[7] = 8'd46;
_autortl_exp_out_data[8] = 8'd17;
_autortl_exp_out_data[9] = 8'd42;
_autortl_exp_out_data[10] = 8'd50;
_autortl_exp_out_data[11] = 8'd181;
_autortl_exp_out_data[12] = 8'd121;
_autortl_exp_out_data[13] = 8'd8;
_autortl_exp_out_data[14] = 8'd15;
_autortl_exp_out_data[15] = 8'd8;
_autortl_exp_out_data[16] = 8'd177;
_autortl_exp_out_data[17] = 8'd247;
_autortl_exp_out_data[18] = 8'd237;
_autortl_exp_out_data[19] = 8'd76;
_autortl_exp_out_data[20] = 8'd46;
_autortl_exp_out_data[21] = 8'd93;
_autortl_exp_out_data[22] = 8'd58;
_autortl_exp_out_data[23] = 8'd7;
_autortl_exp_out_data[24] = 8'd249;
_autortl_exp_out_data[25] = 8'd127;
_autortl_exp_out_data[26] = 8'd33;
_autortl_exp_out_data[27] = 8'd238;
_autortl_exp_out_data[28] = 8'd35;
_autortl_exp_out_data[29] = 8'd45;
_autortl_exp_out_data[30] = 8'd23;
_autortl_exp_out_data[31] = 8'd138;
_autortl_exp_out_data[32] = 8'd32;
_autortl_exp_out_data[33] = 8'd154;
_autortl_exp_out_data[34] = 8'd246;
_autortl_exp_out_data[35] = 8'd181;
_autortl_exp_out_data[36] = 8'd136;
_autortl_exp_out_data[37] = 8'd127;
_autortl_exp_out_data[38] = 8'd102;
_autortl_exp_out_data[39] = 8'd232;
_autortl_exp_out_data[40] = 8'd9;
_autortl_exp_out_data[41] = 8'd36;
_autortl_exp_out_data[42] = 8'd2;
_autortl_exp_out_data[43] = 8'd170;
_autortl_exp_out_data[44] = 8'd73;
_autortl_exp_out_data[45] = 8'd242;
_autortl_exp_out_data[46] = 8'd193;
_autortl_exp_out_data[47] = 8'd85;
_autortl_exp_out_data[48] = 8'd27;
_autortl_exp_out_data[49] = 8'd39;
_autortl_exp_out_data[50] = 8'd254;
_autortl_exp_out_data[51] = 8'd83;
_autortl_exp_out_data[52] = 8'd38;
_autortl_exp_out_data[53] = 8'd110;
_autortl_exp_out_data[54] = 8'd73;
_autortl_exp_out_data[55] = 8'd13;
_autortl_exp_out_data[56] = 8'd177;
_autortl_exp_out_data[57] = 8'd56;
_autortl_exp_out_data[58] = 8'd72;
_autortl_exp_out_data[59] = 8'd156;
_autortl_exp_out_data[60] = 8'd232;
_autortl_exp_out_data[61] = 8'd20;
_autortl_exp_out_data[62] = 8'd213;
_autortl_exp_out_data[63] = 8'd141;
_autortl_exp_out_data[64] = 8'd20;
_autortl_exp_out_data[65] = 8'd90;
_autortl_exp_out_data[66] = 8'd139;
_autortl_exp_out_data[67] = 8'd79;
_autortl_exp_out_data[68] = 8'd153;
_autortl_exp_out_data[69] = 8'd79;
_autortl_exp_out_data[70] = 8'd237;
_autortl_exp_out_data[71] = 8'd21;
_autortl_exp_out_data[72] = 8'd197;
_autortl_exp_out_data[73] = 8'd178;
_autortl_exp_out_data[74] = 8'd253;
_autortl_exp_out_data[75] = 8'd174;
_autortl_exp_out_data[76] = 8'd239;
_autortl_exp_out_data[77] = 8'd243;
_autortl_exp_out_data[78] = 8'd23;
_autortl_exp_out_data[79] = 8'd241;
_autortl_exp_out_data[80] = 8'd87;
_autortl_exp_out_data[81] = 8'd225;
_autortl_exp_out_data[82] = 8'd224;
_autortl_exp_out_data[83] = 8'd151;
_autortl_exp_out_data[84] = 8'd140;
_autortl_exp_out_data[85] = 8'd63;
_autortl_exp_out_data[86] = 8'd95;
_autortl_exp_out_data[87] = 8'd213;
_autortl_exp_out_data[88] = 8'd223;
_autortl_exp_out_data[89] = 8'd61;
_autortl_exp_out_data[90] = 8'd52;
_autortl_exp_out_data[91] = 8'd248;
_autortl_exp_out_data[92] = 8'd192;
_autortl_exp_out_data[93] = 8'd130;
_autortl_exp_out_data[94] = 8'd98;
_autortl_exp_out_data[95] = 8'd176;
_autortl_exp_out_data[96] = 8'd55;
_autortl_exp_out_data[97] = 8'd80;
_autortl_exp_out_data[98] = 8'd137;
_autortl_exp_out_data[99] = 8'd79;
_autortl_exp_out_data[100] = 8'd165;
_autortl_exp_out_data[101] = 8'd228;
_autortl_exp_out_data[102] = 8'd36;
_autortl_exp_out_data[103] = 8'd40;
rst = 1'b1;
repeat (3) @(posedge _autortl_clk);
@(negedge _autortl_clk);
rst = 1'b0;
_autortl_push=0; _autortl_pop=0; _autortl_drain=0; _autortl_stalled=0; _autortl_input_stalled=0; _autortl_noise=0;
for (_autortl_cycle=0; _autortl_cycle<1384 && _autortl_drain<4; _autortl_cycle=_autortl_cycle+1) begin
if (_autortl_cycle > 0) @(negedge _autortl_clk);
out_ready = (_autortl_cycle % 7 >= 2); // periodic backpressure
if (!_autortl_input_stalled) begin
in_valid = (_autortl_push < 104 && _autortl_cycle % 5 != 0);
if (in_valid) begin
in_data = _autortl_stim_in_data[_autortl_push];
end else begin
_autortl_noise = !_autortl_noise;
in_data = _autortl_noise ? 8'd255 : 8'd0;
end
end
if (_autortl_push > 0 && (_autortl_push < 104 || _autortl_pop < _autortl_push) && _autortl_cycle % 11 == 5) begin
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
if (out_data !== _autortl_held_out_data) begin $display("FAIL unstable out_data"); _autortl_errors=_autortl_errors+1; end
end
if (in_valid === 1'b1 && in_ready === 1'b1) begin
_autortl_accepted_cycle[_autortl_push]=_autortl_cycle;
_autortl_push=_autortl_push+1; end
if (out_valid === 1'b1 && out_ready === 1'b1) begin
if (_autortl_pop >= _autortl_push || _autortl_pop >= 104) begin
$display("FAIL unexpected output transaction"); _autortl_errors=_autortl_errors+1;
end else begin
if (_autortl_cycle - _autortl_accepted_cycle[_autortl_pop] < 1) begin
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
initial begin #14070; $display("TEST FAILED: watchdog timeout"); $finish; end
endmodule
