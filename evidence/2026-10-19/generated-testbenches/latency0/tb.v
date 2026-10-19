`timescale 1ns/1ps
module latency0_tb;
reg _autortl_clk = 0;
always #5 _autortl_clk = ~_autortl_clk;
reg [7:0] a;
reg [7:0] b;
wire [7:0] y;
wire [7:0] z;
integer _autortl_cycle, _autortl_errors, _autortl_index;

reg [7:0] _autortl_stim_a [0:7];
reg [7:0] _autortl_stim_b [0:7];
reg [7:0] _autortl_exp_y [0:7];
reg [7:0] _autortl_exp_z [0:7];
latency0 dut (.a(a), .b(b), .y(y), .z(z));
initial begin
_autortl_errors = 0;
a = 0;
b = 0;
_autortl_stim_a[0] = 8'd0;
_autortl_stim_a[1] = 8'd1;
_autortl_stim_a[2] = 8'd255;
_autortl_stim_a[3] = 8'd3;
_autortl_stim_a[4] = 8'd8;
_autortl_stim_a[5] = 8'd17;
_autortl_stim_a[6] = 8'd10;
_autortl_stim_a[7] = 8'd5;
_autortl_stim_b[0] = 8'd0;
_autortl_stim_b[1] = 8'd2;
_autortl_stim_b[2] = 8'd1;
_autortl_stim_b[3] = 8'd7;
_autortl_stim_b[4] = 8'd4;
_autortl_stim_b[5] = 8'd9;
_autortl_stim_b[6] = 8'd22;
_autortl_stim_b[7] = 8'd6;
_autortl_exp_y[0] = 8'd0;
_autortl_exp_y[1] = 8'd3;
_autortl_exp_y[2] = 8'd0;
_autortl_exp_y[3] = 8'd10;
_autortl_exp_y[4] = 8'd12;
_autortl_exp_y[5] = 8'd26;
_autortl_exp_y[6] = 8'd32;
_autortl_exp_y[7] = 8'd11;
_autortl_exp_z[0] = 8'd0;
_autortl_exp_z[1] = 8'd3;
_autortl_exp_z[2] = 8'd254;
_autortl_exp_z[3] = 8'd4;
_autortl_exp_z[4] = 8'd12;
_autortl_exp_z[5] = 8'd24;
_autortl_exp_z[6] = 8'd28;
_autortl_exp_z[7] = 8'd3;
@(negedge _autortl_clk);
for (_autortl_cycle=0; _autortl_cycle<8; _autortl_cycle=_autortl_cycle+1) begin
if (_autortl_cycle > 0) @(negedge _autortl_clk);
if (_autortl_cycle < 8) begin
a = _autortl_stim_a[_autortl_cycle];
b = _autortl_stim_b[_autortl_cycle];
end
#1;
_autortl_index = _autortl_cycle - 0;
if (_autortl_index >= 0 && _autortl_index < 8) begin
if (y !== _autortl_exp_y[_autortl_index]) begin $display("FAIL index=%0d signal=y", _autortl_index); _autortl_errors = _autortl_errors + 1; end
if (z !== _autortl_exp_z[_autortl_index]) begin $display("FAIL index=%0d signal=z", _autortl_index); _autortl_errors = _autortl_errors + 1; end
end
end
if (_autortl_errors == 0) $display("TEST PASSED");
else $display("TEST FAILED: %0d errors", _autortl_errors);
$finish;
end
initial begin #330; $display("TEST FAILED: watchdog timeout"); $finish; end
endmodule
