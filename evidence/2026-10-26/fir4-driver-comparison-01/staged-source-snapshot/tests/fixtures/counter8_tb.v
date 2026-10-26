`timescale 1ns/1ps
module counter8_tb;
    reg clk = 0;
    reg rst = 1;
    reg enable = 0;
    wire [7:0] count;
    reg [7:0] expected = 0;
    integer errors = 0;
    integer i;
    counter8 dut(.clk(clk), .rst(rst), .enable(enable), .count(count));
    always #5 clk = ~clk;
    initial begin
        for (i = 0; i < 700; i = i + 1) begin
            @(negedge clk);
            rst = (i < 3) || (i == 420);
            enable = (i < 310) || (i % 7 != 0);
            if (i == 420) begin
                #1;
                if (count !== expected) begin
                    errors = errors + 1;
                    $display("FAIL reset changed count before clock edge");
                end
            end
            @(posedge clk);
            if (rst) expected = 0;
            else if (enable) expected = expected + 1;
            #1;
            if (count !== expected) begin
                errors = errors + 1;
                if (errors <= 8) $display("FAIL cycle=%0d expected=%0d got=%0d", i, expected, count);
            end
        end
        if (errors == 0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end
    initial begin
        #10000;
        $display("TEST FAILED: watchdog");
        $finish;
    end
endmodule
