`timescale 1ns/1ps
module stateful_counter_tb;
reg _autortl_clk = 0;
always #5 _autortl_clk = ~_autortl_clk;
reg [0:0] rst;
reg [0:0] en;
wire [7:0] count;
integer _autortl_cycle, _autortl_errors, _autortl_index;

reg [0:0] _autortl_stim_en [0:5];
reg [7:0] _autortl_exp_count [0:5];
stateful_counter dut (.clk(_autortl_clk), .rst(rst), .en(en), .count(count));
initial begin
_autortl_errors = 0;
rst = 0;
en = 0;
_autortl_stim_en[0] = 1'd1;
_autortl_stim_en[1] = 1'd1;
_autortl_stim_en[2] = 1'd0;
_autortl_stim_en[3] = 1'd1;
_autortl_stim_en[4] = 1'd0;
_autortl_stim_en[5] = 1'd1;
_autortl_exp_count[0] = 8'd1;
_autortl_exp_count[1] = 8'd2;
_autortl_exp_count[2] = 8'd2;
_autortl_exp_count[3] = 8'd3;
_autortl_exp_count[4] = 8'd3;
_autortl_exp_count[5] = 8'd4;
rst = 1'b1;
repeat (5) @(posedge _autortl_clk);
@(negedge _autortl_clk);
rst = 1'b0;
for (_autortl_cycle=0; _autortl_cycle<6; _autortl_cycle=_autortl_cycle+1) begin
if (_autortl_cycle > 0) @(negedge _autortl_clk);
if (_autortl_cycle < 6) begin
en = _autortl_stim_en[_autortl_cycle];
end
@(posedge _autortl_clk);
#1;
_autortl_index = _autortl_cycle - 0;
if (_autortl_index >= 0 && _autortl_index < 6) begin
if (count !== _autortl_exp_count[_autortl_index]) begin $display("FAIL index=%0d signal=count", _autortl_index); _autortl_errors = _autortl_errors + 1; end
end
end
if (_autortl_errors == 0) $display("TEST PASSED");
else $display("TEST FAILED: %0d errors", _autortl_errors);
$finish;
end
initial begin #310; $display("TEST FAILED: watchdog timeout"); $finish; end
endmodule
