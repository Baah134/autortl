`timescale 1ns/1ps
module accumulated_cell_tb;
reg _autortl_clk = 0;
always #5 _autortl_clk = ~_autortl_clk;
reg rst;
reg [7:0] amount;
wire [7:0] total;
integer _autortl_cycle, _autortl_errors, _autortl_index;

reg [7:0] _autortl_stim_amount [0:3];
reg [7:0] _autortl_exp_total [0:3];
accumulated_cell dut (.clk(_autortl_clk), .rst(rst), .amount(amount), .total(total));
initial begin
_autortl_errors = 0;
rst = 0;
amount = 0;
_autortl_stim_amount[0] = 8'd0;
_autortl_stim_amount[1] = 8'd1;
_autortl_stim_amount[2] = 8'd7;
_autortl_stim_amount[3] = 8'd3;
_autortl_exp_total[0] = 8'd0;
_autortl_exp_total[1] = 8'd1;
_autortl_exp_total[2] = 8'd8;
_autortl_exp_total[3] = 8'd11;
rst = 1'b1;
repeat (5) @(posedge _autortl_clk);
@(negedge _autortl_clk);
rst = 1'b0;
for (_autortl_cycle=0; _autortl_cycle<4; _autortl_cycle=_autortl_cycle+1) begin
if (_autortl_cycle > 0) @(negedge _autortl_clk);
if (_autortl_cycle < 4) begin
amount = _autortl_stim_amount[_autortl_cycle];
end
@(posedge _autortl_clk);
#1;
_autortl_index = _autortl_cycle - 0;
if (_autortl_index >= 0 && _autortl_index < 4) begin
if (total !== _autortl_exp_total[_autortl_index]) begin $display("FAIL index=%0d signal=total", _autortl_index); _autortl_errors = _autortl_errors + 1; end
end
end
if (_autortl_errors == 0) $display("TEST PASSED");
else $display("TEST FAILED: %0d errors", _autortl_errors);
$finish;
end
initial begin #290; $display("TEST FAILED: watchdog timeout"); $finish; end
endmodule
