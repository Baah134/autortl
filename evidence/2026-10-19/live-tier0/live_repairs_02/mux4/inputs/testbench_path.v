`timescale 1ns/1ps
module mux4_tb;
    reg clk, rst;
    reg [7:0] a, b, c, d;
    reg [1:0] sel;
    wire [7:0] y;
    integer errors;
    mux4 dut(.clk(clk), .rst(rst), .a(a), .b(b), .c(c), .d(d), .sel(sel), .y(y));
    always #5 clk = ~clk;
    initial begin
        clk=0; errors=0; rst=1; a=8'd10; b=8'd20; c=8'd30; d=8'd40; sel=0;
        repeat(3) @(posedge clk); rst=0;
        sel=2'd0; @(posedge clk); @(posedge clk); #1;
        if (y !== 8'd10) begin $display("FAIL: sel=0 expected=10 got=%0d", y); errors=errors+1; end
        sel=2'd1; @(posedge clk); @(posedge clk); #1;
        if (y !== 8'd20) begin $display("FAIL: sel=1 expected=20 got=%0d", y); errors=errors+1; end
        sel=2'd2; @(posedge clk); @(posedge clk); #1;
        if (y !== 8'd30) begin $display("FAIL: sel=2 expected=30 got=%0d", y); errors=errors+1; end
        sel=2'd3; @(posedge clk); @(posedge clk); #1;
        if (y !== 8'd40) begin $display("FAIL: sel=3 expected=40 got=%0d", y); errors=errors+1; end
        if (errors==0) $display("TEST PASSED"); else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end
endmodule
