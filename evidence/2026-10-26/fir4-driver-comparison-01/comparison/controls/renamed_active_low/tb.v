`timescale 1ns/1ps
module driver_renamed_active_low_tb;
reg _autortl_clk = 0;
always #5 _autortl_clk = ~_autortl_clk;
reg reset_n;
reg [7:0] a;
reg [4:0] b;
wire [7:0] y;
wire [7:0] z;
reg request_valid;
wire request_ready;
wire response_valid;
reg response_ready;
integer _autortl_cycle, _autortl_errors, _autortl_index;
integer _autortl_push, _autortl_pop, _autortl_drain;
reg _autortl_stalled;
reg _autortl_input_stalled, _autortl_noise;
integer _autortl_accepted_cycle [0:39];
reg [7:0] _autortl_held_y;
reg [7:0] _autortl_held_z;
reg [7:0] _autortl_stim_a [0:39];
reg [4:0] _autortl_stim_b [0:39];
reg [7:0] _autortl_exp_y [0:39];
reg [7:0] _autortl_exp_z [0:39];
driver_renamed_active_low dut (.clk(_autortl_clk), .reset_n(reset_n), .a(a), .b(b), .y(y), .z(z), .request_valid(request_valid), .request_ready(request_ready), .response_valid(response_valid), .response_ready(response_ready));
integer probe_cycle,probe_accepted,probe_retired,probe_invalid_before_accept;
integer probe_invalid_followed_by_accept,probe_noise_changes,probe_blocked,probe_longest_block;
integer probe_block_run,probe_release_on_bubble,probe_pulses,probe_edge_resets;
integer probe_producer_errors,probe_timing_errors;
reg probe_waiting,probe_invalid_pending,probe_invalid_seen,probe_started,probe_pulse_open;
reg [12:0] probe_held_payload,probe_last_invalid;
reg [14:0] probe_pulse_inputs;
realtime probe_last_fall,probe_assert_time;
initial begin
 probe_cycle=0;probe_accepted=0;probe_retired=0;probe_invalid_before_accept=0;
 probe_invalid_followed_by_accept=0;probe_noise_changes=0;probe_blocked=0;probe_longest_block=0;
 probe_block_run=0;probe_release_on_bubble=0;probe_pulses=0;probe_edge_resets=0;
 probe_producer_errors=0;probe_timing_errors=0;probe_waiting=0;probe_invalid_pending=0;
 probe_invalid_seen=0;probe_started=0;probe_pulse_open=0;probe_held_payload=0;
 probe_last_invalid=0;probe_pulse_inputs=0;probe_last_fall=0;probe_assert_time=0;
end
always @(negedge _autortl_clk) probe_last_fall=$realtime;
always @(posedge _autortl_clk) begin
 if(reset_n === 1'b0) begin
  probe_waiting=0;
  if(probe_started) begin
   probe_edge_resets=probe_edge_resets+1;
   $display("FAIL DRIVER pulse overlaps rising edge");probe_timing_errors=probe_timing_errors+1;
  end
 end else begin
  probe_started=1;
  if(probe_pulse_open) begin
   $display("FAIL DRIVER pulse still open at rising edge");probe_timing_errors=probe_timing_errors+1;
  end
  if(probe_waiting) begin
   if(request_valid !== 1'b1 || {a,b} !== probe_held_payload) begin
    $display("FAIL DRIVER producer changed blocked offer cycle=%0d",probe_cycle);
    probe_producer_errors=probe_producer_errors+1;
   end
   if(request_ready === 1'b1 && probe_cycle%5==0) probe_release_on_bubble=probe_release_on_bubble+1;
  end
  if(request_valid === 1'b0 && probe_accepted<40) begin
   probe_invalid_before_accept=probe_invalid_before_accept+1;probe_invalid_pending=1;
   if(probe_invalid_seen && {a,b} !== probe_last_invalid) probe_noise_changes=probe_noise_changes+1;
   probe_invalid_seen=1;probe_last_invalid={a,b};
  end
  if(request_valid === 1'b1 && request_ready === 1'b1) begin
   probe_accepted=probe_accepted+1;
   if(probe_invalid_pending) probe_invalid_followed_by_accept=probe_invalid_followed_by_accept+1;
   probe_invalid_pending=0;
  end
  if(response_valid === 1'b1 && response_ready === 1'b1) probe_retired=probe_retired+1;
  probe_waiting=(request_valid === 1'b1 && request_ready === 1'b0);probe_held_payload={a,b};
  if(probe_waiting) begin
   probe_blocked=probe_blocked+1;probe_block_run=probe_block_run+1;
   if(probe_block_run>probe_longest_block) probe_longest_block=probe_block_run;
  end else probe_block_run=0;
  probe_cycle=probe_cycle+1;
 end
end
always @(reset_n) begin
 if(probe_started && reset_n === 1'b0) begin
  probe_pulses=probe_pulses+1;probe_pulse_open=1;probe_assert_time=$realtime;
  probe_pulse_inputs={a,b,request_valid,response_ready};
  if($realtime-probe_last_fall < 0.99 || $realtime-probe_last_fall > 1.01) begin
   $display("FAIL DRIVER pulse assertion phase");probe_timing_errors=probe_timing_errors+1;
  end
 end else if(probe_pulse_open && reset_n === 1'b1) begin
  if($realtime-probe_assert_time < 1.99 || $realtime-probe_assert_time > 2.01 ||
     $realtime-probe_last_fall < 2.99 || $realtime-probe_last_fall > 3.01 ||
     {a,b,request_valid,response_ready} !== probe_pulse_inputs) begin
   $display("FAIL DRIVER pulse duration or held inputs");probe_timing_errors=probe_timing_errors+1;
  end
  probe_pulse_open=0;
 end
end
always @(a or b or request_valid or response_ready) begin
 if(probe_pulse_open && {a,b,request_valid,response_ready} !== probe_pulse_inputs) begin
  $display("FAIL DRIVER input changed during pulse");probe_timing_errors=probe_timing_errors+1;
 end
end
initial begin
_autortl_errors = 0;
reset_n = 0;
a = 0;
b = 0;
request_valid = 0;
response_ready = 0;
_autortl_stim_a[0] = 8'd0;
_autortl_stim_a[1] = 8'd255;
_autortl_stim_a[2] = 8'd128;
_autortl_stim_a[3] = 8'd3;
_autortl_stim_a[4] = 8'd40;
_autortl_stim_a[5] = 8'd77;
_autortl_stim_a[6] = 8'd114;
_autortl_stim_a[7] = 8'd151;
_autortl_stim_a[8] = 8'd188;
_autortl_stim_a[9] = 8'd225;
_autortl_stim_a[10] = 8'd6;
_autortl_stim_a[11] = 8'd43;
_autortl_stim_a[12] = 8'd80;
_autortl_stim_a[13] = 8'd117;
_autortl_stim_a[14] = 8'd154;
_autortl_stim_a[15] = 8'd191;
_autortl_stim_a[16] = 8'd228;
_autortl_stim_a[17] = 8'd9;
_autortl_stim_a[18] = 8'd46;
_autortl_stim_a[19] = 8'd83;
_autortl_stim_a[20] = 8'd120;
_autortl_stim_a[21] = 8'd157;
_autortl_stim_a[22] = 8'd194;
_autortl_stim_a[23] = 8'd231;
_autortl_stim_a[24] = 8'd12;
_autortl_stim_a[25] = 8'd49;
_autortl_stim_a[26] = 8'd86;
_autortl_stim_a[27] = 8'd123;
_autortl_stim_a[28] = 8'd160;
_autortl_stim_a[29] = 8'd197;
_autortl_stim_a[30] = 8'd234;
_autortl_stim_a[31] = 8'd15;
_autortl_stim_a[32] = 8'd52;
_autortl_stim_a[33] = 8'd89;
_autortl_stim_a[34] = 8'd126;
_autortl_stim_a[35] = 8'd163;
_autortl_stim_a[36] = 8'd200;
_autortl_stim_a[37] = 8'd237;
_autortl_stim_a[38] = 8'd18;
_autortl_stim_a[39] = 8'd55;
_autortl_stim_b[0] = 5'd0;
_autortl_stim_b[1] = 5'd31;
_autortl_stim_b[2] = 5'd17;
_autortl_stim_b[3] = 5'd5;
_autortl_stim_b[4] = 5'd16;
_autortl_stim_b[5] = 5'd27;
_autortl_stim_b[6] = 5'd6;
_autortl_stim_b[7] = 5'd17;
_autortl_stim_b[8] = 5'd28;
_autortl_stim_b[9] = 5'd7;
_autortl_stim_b[10] = 5'd18;
_autortl_stim_b[11] = 5'd29;
_autortl_stim_b[12] = 5'd8;
_autortl_stim_b[13] = 5'd19;
_autortl_stim_b[14] = 5'd30;
_autortl_stim_b[15] = 5'd9;
_autortl_stim_b[16] = 5'd20;
_autortl_stim_b[17] = 5'd31;
_autortl_stim_b[18] = 5'd10;
_autortl_stim_b[19] = 5'd21;
_autortl_stim_b[20] = 5'd0;
_autortl_stim_b[21] = 5'd11;
_autortl_stim_b[22] = 5'd22;
_autortl_stim_b[23] = 5'd1;
_autortl_stim_b[24] = 5'd12;
_autortl_stim_b[25] = 5'd23;
_autortl_stim_b[26] = 5'd2;
_autortl_stim_b[27] = 5'd13;
_autortl_stim_b[28] = 5'd24;
_autortl_stim_b[29] = 5'd3;
_autortl_stim_b[30] = 5'd14;
_autortl_stim_b[31] = 5'd25;
_autortl_stim_b[32] = 5'd4;
_autortl_stim_b[33] = 5'd15;
_autortl_stim_b[34] = 5'd26;
_autortl_stim_b[35] = 5'd5;
_autortl_stim_b[36] = 5'd16;
_autortl_stim_b[37] = 5'd27;
_autortl_stim_b[38] = 5'd6;
_autortl_stim_b[39] = 5'd17;
_autortl_exp_y[0] = 8'd0;
_autortl_exp_y[1] = 8'd30;
_autortl_exp_y[2] = 8'd145;
_autortl_exp_y[3] = 8'd8;
_autortl_exp_y[4] = 8'd56;
_autortl_exp_y[5] = 8'd104;
_autortl_exp_y[6] = 8'd120;
_autortl_exp_y[7] = 8'd168;
_autortl_exp_y[8] = 8'd216;
_autortl_exp_y[9] = 8'd232;
_autortl_exp_y[10] = 8'd24;
_autortl_exp_y[11] = 8'd72;
_autortl_exp_y[12] = 8'd88;
_autortl_exp_y[13] = 8'd136;
_autortl_exp_y[14] = 8'd184;
_autortl_exp_y[15] = 8'd200;
_autortl_exp_y[16] = 8'd248;
_autortl_exp_y[17] = 8'd40;
_autortl_exp_y[18] = 8'd56;
_autortl_exp_y[19] = 8'd104;
_autortl_exp_y[20] = 8'd120;
_autortl_exp_y[21] = 8'd168;
_autortl_exp_y[22] = 8'd216;
_autortl_exp_y[23] = 8'd232;
_autortl_exp_y[24] = 8'd24;
_autortl_exp_y[25] = 8'd72;
_autortl_exp_y[26] = 8'd88;
_autortl_exp_y[27] = 8'd136;
_autortl_exp_y[28] = 8'd184;
_autortl_exp_y[29] = 8'd200;
_autortl_exp_y[30] = 8'd248;
_autortl_exp_y[31] = 8'd40;
_autortl_exp_y[32] = 8'd56;
_autortl_exp_y[33] = 8'd104;
_autortl_exp_y[34] = 8'd152;
_autortl_exp_y[35] = 8'd168;
_autortl_exp_y[36] = 8'd216;
_autortl_exp_y[37] = 8'd8;
_autortl_exp_y[38] = 8'd24;
_autortl_exp_y[39] = 8'd72;
_autortl_exp_z[0] = 8'd0;
_autortl_exp_z[1] = 8'd224;
_autortl_exp_z[2] = 8'd145;
_autortl_exp_z[3] = 8'd6;
_autortl_exp_z[4] = 8'd56;
_autortl_exp_z[5] = 8'd86;
_autortl_exp_z[6] = 8'd116;
_autortl_exp_z[7] = 8'd134;
_autortl_exp_z[8] = 8'd160;
_autortl_exp_z[9] = 8'd230;
_autortl_exp_z[10] = 8'd20;
_autortl_exp_z[11] = 8'd54;
_autortl_exp_z[12] = 8'd88;
_autortl_exp_z[13] = 8'd102;
_autortl_exp_z[14] = 8'd132;
_autortl_exp_z[15] = 8'd182;
_autortl_exp_z[16] = 8'd240;
_autortl_exp_z[17] = 8'd22;
_autortl_exp_z[18] = 8'd36;
_autortl_exp_z[19] = 8'd70;
_autortl_exp_z[20] = 8'd120;
_autortl_exp_z[21] = 8'd150;
_autortl_exp_z[22] = 8'd212;
_autortl_exp_z[23] = 8'd230;
_autortl_exp_z[24] = 8'd0;
_autortl_exp_z[25] = 8'd38;
_autortl_exp_z[26] = 8'd84;
_autortl_exp_z[27] = 8'd118;
_autortl_exp_z[28] = 8'd184;
_autortl_exp_z[29] = 8'd198;
_autortl_exp_z[30] = 8'd228;
_autortl_exp_z[31] = 8'd22;
_autortl_exp_z[32] = 8'd48;
_autortl_exp_z[33] = 8'd86;
_autortl_exp_z[34] = 8'd100;
_autortl_exp_z[35] = 8'd166;
_autortl_exp_z[36] = 8'd216;
_autortl_exp_z[37] = 8'd246;
_autortl_exp_z[38] = 8'd20;
_autortl_exp_z[39] = 8'd38;
reset_n = 1'b0;
repeat (3) @(posedge _autortl_clk);
@(negedge _autortl_clk);
reset_n = 1'b1;
_autortl_push=0; _autortl_pop=0; _autortl_drain=0; _autortl_stalled=0; _autortl_input_stalled=0; _autortl_noise=0;
for (_autortl_cycle=0; _autortl_cycle<552 && _autortl_drain<4; _autortl_cycle=_autortl_cycle+1) begin
if (_autortl_cycle > 0) @(negedge _autortl_clk);
response_ready = (_autortl_cycle % 7 >= 2); // periodic backpressure
if (!_autortl_input_stalled) begin
request_valid = (_autortl_push < 40 && _autortl_cycle % 5 != 0);
if (request_valid) begin
a = _autortl_stim_a[_autortl_push];
b = _autortl_stim_b[_autortl_push];
end else begin
_autortl_noise = !_autortl_noise;
a = _autortl_noise ? 8'd255 : 8'd0;
b = _autortl_noise ? 5'd31 : 5'd0;
end
end
if (_autortl_push > 0 && (_autortl_push < 40 || _autortl_pop < _autortl_push) && _autortl_cycle % 11 == 5) begin
// complete off-edge pulse; all other inputs stay held
#1; reset_n = 1'b0;
#2; reset_n = 1'b1;
end
@(posedge _autortl_clk); // sample accepted transfers BEFORE NBA
if ((request_ready !== 1'b0 && request_ready !== 1'b1) || (response_valid !== 1'b0 && response_valid !== 1'b1)) begin
$display("FAIL unknown handshake"); _autortl_errors=_autortl_errors+1; end
_autortl_input_stalled=(request_valid === 1'b1 && request_ready === 1'b0);
if (_autortl_stalled) begin
if (response_valid !== 1'b1) begin $display("FAIL valid dropped under backpressure"); _autortl_errors=_autortl_errors+1; end
if (y !== _autortl_held_y) begin $display("FAIL unstable y"); _autortl_errors=_autortl_errors+1; end
if (z !== _autortl_held_z) begin $display("FAIL unstable z"); _autortl_errors=_autortl_errors+1; end
end
if (request_valid === 1'b1 && request_ready === 1'b1) begin
_autortl_accepted_cycle[_autortl_push]=_autortl_cycle;
_autortl_push=_autortl_push+1; end
if (response_valid === 1'b1 && response_ready === 1'b1) begin
if (_autortl_pop >= _autortl_push || _autortl_pop >= 40) begin
$display("FAIL unexpected output transaction"); _autortl_errors=_autortl_errors+1;
end else begin
if (_autortl_cycle - _autortl_accepted_cycle[_autortl_pop] < 1) begin
$display("FAIL output before minimum transfer latency"); _autortl_errors=_autortl_errors+1; end
if (y !== _autortl_exp_y[_autortl_pop]) begin $display("FAIL index=%0d signal=y", _autortl_pop); _autortl_errors = _autortl_errors + 1; end
if (z !== _autortl_exp_z[_autortl_pop]) begin $display("FAIL index=%0d signal=z", _autortl_pop); _autortl_errors = _autortl_errors + 1; end
end
_autortl_pop=_autortl_pop+1;
end
_autortl_stalled=(response_valid === 1'b1 && response_ready === 1'b0);
_autortl_held_y=y;
_autortl_held_z=z;
if (_autortl_pop >= 40) _autortl_drain=_autortl_drain+1;
end
if (_autortl_push != 40 || _autortl_pop != 40) begin
$display("FAIL scoreboard did not drain"); _autortl_errors=_autortl_errors+1; end
#0.001; // let the independent observation processes finish this edge
$display("DRIVER_COVERAGE case=renamed_active_low accepted=%0d retired=%0d invalid_before_accept=%0d invalid_followed_by_accept=%0d noise_changes=%0d blocked=%0d longest_block=%0d release_on_bubble=%0d pulses=%0d edge_resets=%0d producer_errors=%0d timing_errors=%0d",probe_accepted,probe_retired,probe_invalid_before_accept,probe_invalid_followed_by_accept,probe_noise_changes,probe_blocked,probe_longest_block,probe_release_on_bubble,probe_pulses,probe_edge_resets,probe_producer_errors,probe_timing_errors);
if(probe_invalid_before_accept==0 || probe_invalid_followed_by_accept==0 || probe_noise_changes==0) $display("COVERAGE_MISSING driver invalid traffic");
if(probe_producer_errors || probe_timing_errors) _autortl_errors=_autortl_errors+probe_producer_errors+probe_timing_errors;
if (_autortl_errors == 0) $display("TEST PASSED");
else $display("TEST FAILED: %0d errors", _autortl_errors);
$finish;
end
initial begin #5750; $display("TEST FAILED: watchdog timeout"); $finish; end
endmodule
