`timescale 1ns/1ps
module counter_tb;
    reg clk, rst, enable, load;
    reg  [31:0] load_val;
    wire [31:0] count;
    wire at_zero, below_low, below_mid, below_high, overflow;
    integer errors;

    counter dut (.clk(clk), .rst(rst), .enable(enable), .load(load),
                 .load_val(load_val), .count(count), .at_zero(at_zero),
                 .below_low(below_low), .below_mid(below_mid),
                 .below_high(below_high), .overflow(overflow));

    always #5 clk = ~clk;

    task check(input cond, input [255:0] msg);
        if (!cond) begin
            $display("FAIL: %0s", msg);
            errors = errors + 1;
        end
    endtask

    initial begin
        clk = 0; errors = 0; rst = 1; enable = 0; load = 0; load_val = 0;
        repeat (4) @(posedge clk);
        rst = 0; @(posedge clk); #1;

        // T1 reset state (flags combinational OR registered both settle by here)
        check(count == 0, "count not zero after reset");
        @(posedge clk); #1;
        check(at_zero == 1, "at_zero should be 1 when count=0");
        check(below_low == 1, "below_low should be 1 when count=0");

        // T2 count up to 150
        enable = 1;
        repeat (150) @(posedge clk);
        #1; @(posedge clk); #1;   // allow one extra cycle for registered flags
        check(count == 150, "count should be 150");
        check(below_mid == 1, "below_mid should be 1 when count=150");
        check(below_low == 0, "below_low should be 0 when count=150");

        // T3 hold when disabled
        enable = 0;
        repeat (5) @(posedge clk); #1;
        check(count == 150, "count changed while disabled");

        // T4 load
        load = 1; load_val = 32'd1000;
        @(posedge clk); #1; load = 0;
        check(count == 1000, "load failed");
        @(posedge clk); #1;
        check(below_high == 0, "below_high should be 0 at 1000");

        // T5 overflow wrap
        load = 1; load_val = 32'hFFFFFFFE; @(posedge clk); #1; load = 0;
        enable = 1;
        @(posedge clk); #1;   // -> FFFFFFFF
        @(posedge clk); #1;   // -> 0 + overflow pulse
        check(count == 0, "should wrap to 0 on overflow");
        check(overflow == 1, "overflow flag not set");
        enable = 0;

        if (errors == 0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end
endmodule
