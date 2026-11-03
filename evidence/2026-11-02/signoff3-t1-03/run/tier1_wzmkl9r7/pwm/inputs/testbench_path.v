`timescale 1ns/1ps
module pwm_tb;
    reg clk, rst; reg [7:0] duty; wire pwm_out;
    integer errors, i, highs;
    pwm dut(.clk(clk), .rst(rst), .duty(duty), .pwm_out(pwm_out));
    always #5 clk = ~clk;
    initial begin
        clk=0; errors=0; rst=1; duty=8'd64;
        repeat(4) @(posedge clk); rst=0; @(posedge clk);
        // measure one full 256-cycle period: expect ~64 highs (+-1 for latency)
        highs=0;
        for (i=0; i<256; i=i+1) begin @(posedge clk); #1; if (pwm_out) highs=highs+1; end
        if (highs < 62 || highs > 66) begin
            $display("FAIL: duty=64 expected~64 highs got=%0d", highs); errors=errors+1;
        end
        duty=8'd0; repeat(300) @(posedge clk);
        highs=0;
        for (i=0; i<256; i=i+1) begin @(posedge clk); #1; if (pwm_out) highs=highs+1; end
        if (highs > 1) begin $display("FAIL: duty=0 got=%0d highs", highs); errors=errors+1; end
        if (errors==0) $display("TEST PASSED"); else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end
endmodule
