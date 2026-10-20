`timescale 1ns/1ps
module stream_pair_tb;
reg _autortl_clk = 0;
always #5 _autortl_clk = ~_autortl_clk;
reg rst;
reg [7:0] a;
reg [7:0] b;
wire [7:0] y;
wire [7:0] z;
reg in_valid;
wire in_ready;
wire out_valid;
reg out_ready;
integer _autortl_cycle, _autortl_errors, _autortl_index;
integer _autortl_push, _autortl_pop, _autortl_drain;
reg _autortl_stalled;
integer _autortl_accepted_cycle [0:2];
reg [7:0] _autortl_held_y;
reg [7:0] _autortl_held_z;
reg [7:0] _autortl_stim_a [0:2];
reg [7:0] _autortl_stim_b [0:2];
reg [7:0] _autortl_exp_y [0:2];
reg [7:0] _autortl_exp_z [0:2];
stream_pair dut (.clk(_autortl_clk), .rst(rst), .a(a), .b(b), .y(y), .z(z), .in_valid(in_valid), .in_ready(in_ready), .out_valid(out_valid), .out_ready(out_ready));
initial begin
_autortl_errors = 0;
rst = 0;
a = 0;
b = 0;
in_valid = 0;
out_ready = 0;
_autortl_stim_a[0] = 8'd0;
_autortl_stim_a[1] = 8'd1;
_autortl_stim_a[2] = 8'd2;
_autortl_stim_b[0] = 8'd1;
_autortl_stim_b[1] = 8'd2;
_autortl_stim_b[2] = 8'd3;
_autortl_exp_y[0] = 8'd1;
_autortl_exp_y[1] = 8'd3;
_autortl_exp_y[2] = 8'd5;
_autortl_exp_z[0] = 8'd1;
_autortl_exp_z[1] = 8'd3;
_autortl_exp_z[2] = 8'd1;
rst = 1'b1;
repeat (5) @(posedge _autortl_clk);
@(negedge _autortl_clk);
rst = 1'b0;
_autortl_push=0; _autortl_pop=0; _autortl_drain=0; _autortl_stalled=0;
for (_autortl_cycle=0; _autortl_cycle<368 && _autortl_drain<4; _autortl_cycle=_autortl_cycle+1) begin
if (_autortl_cycle > 0) @(negedge _autortl_clk);
in_valid = (_autortl_push < 3);
out_ready = (_autortl_cycle % 7 >= 2); // periodic backpressure
if (_autortl_push < 3) begin
a = _autortl_stim_a[_autortl_push];
b = _autortl_stim_b[_autortl_push];
end
@(posedge _autortl_clk); // sample accepted transfers BEFORE NBA
if ((in_ready !== 1'b0 && in_ready !== 1'b1) || (out_valid !== 1'b0 && out_valid !== 1'b1)) begin
$display("FAIL unknown handshake"); _autortl_errors=_autortl_errors+1; end
if (_autortl_stalled) begin
if (out_valid !== 1'b1) begin $display("FAIL valid dropped under backpressure"); _autortl_errors=_autortl_errors+1; end
if (y !== _autortl_held_y) begin $display("FAIL unstable y"); _autortl_errors=_autortl_errors+1; end
if (z !== _autortl_held_z) begin $display("FAIL unstable z"); _autortl_errors=_autortl_errors+1; end
end
if (in_valid === 1'b1 && in_ready === 1'b1) begin
_autortl_accepted_cycle[_autortl_push]=_autortl_cycle;
_autortl_push=_autortl_push+1; end
if (out_valid === 1'b1 && out_ready === 1'b1) begin
if (_autortl_pop >= _autortl_push || _autortl_pop >= 3) begin
$display("FAIL unexpected output transaction"); _autortl_errors=_autortl_errors+1;
end else begin
if (_autortl_cycle - _autortl_accepted_cycle[_autortl_pop] < 100) begin
$display("FAIL output before minimum transfer latency"); _autortl_errors=_autortl_errors+1; end
if (y !== _autortl_exp_y[_autortl_pop]) begin $display("FAIL index=%0d signal=y", _autortl_pop); _autortl_errors = _autortl_errors + 1; end
if (z !== _autortl_exp_z[_autortl_pop]) begin $display("FAIL index=%0d signal=z", _autortl_pop); _autortl_errors = _autortl_errors + 1; end
end
_autortl_pop=_autortl_pop+1;
end
_autortl_stalled=(out_valid === 1'b1 && out_ready === 1'b0);
_autortl_held_y=y;
_autortl_held_z=z;
if (_autortl_pop >= 3) _autortl_drain=_autortl_drain+1;
end
if (_autortl_push != 3 || _autortl_pop != 3) begin
$display("FAIL scoreboard did not drain"); _autortl_errors=_autortl_errors+1; end
if (_autortl_errors == 0) $display("TEST PASSED");
else $display("TEST FAILED: %0d errors", _autortl_errors);
$finish;
end
initial begin #3930; $display("TEST FAILED: watchdog timeout"); $finish; end
endmodule
