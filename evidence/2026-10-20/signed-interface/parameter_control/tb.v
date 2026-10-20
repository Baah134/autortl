`timescale 1ns/1ps
module param_shape_tb;
reg signed [12:0] a;
wire signed [0:12] y;
integer errors=0;
param_shape #(.W(12),.EXTRA(1)) dut(.a(a),.y(y));
initial begin
 a=13'h1f03; #2; if(y!==a) begin $display("FAIL nondefault parameter negative bits");errors=errors+1;end
 a=13'd1; #2; if(y!==a) begin $display("FAIL nondefault parameter positive bits");errors=errors+1;end
 a=13'h1fff; #2; if(y!==a) begin $display("FAIL nondefault parameter all ones");errors=errors+1;end
 if(errors==0)$display("TEST PASSED");else $display("TEST FAILED: %0d errors",errors);
 $finish;
end
initial begin #100;$display("TEST FAILED: watchdog");$finish;end
endmodule