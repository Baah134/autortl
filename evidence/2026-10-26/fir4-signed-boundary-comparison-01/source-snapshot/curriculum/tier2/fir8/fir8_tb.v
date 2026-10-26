`timescale 1ns/1ps
module fir8_tb;
    reg clk, rst; reg signed [15:0] x_in; wire signed [31:0] y_out;
    integer errors;
    fir8 dut(.clk(clk), .rst(rst), .x_in(x_in), .y_out(y_out));
    always #5 clk = ~clk;
    // impulse response should replay the coefficients
    integer k;
    reg signed [31:0] expected [0:9];
    initial begin
        expected[0]=3; expected[1]=7; expected[2]=12; expected[3]=18;
        expected[4]=18; expected[5]=12; expected[6]=7; expected[7]=3;
        expected[8]=0; expected[9]=0;
    end
    initial begin
        clk=0; errors=0; rst=1; x_in=0;
        repeat(4) @(posedge clk); rst=0; @(posedge clk);
        x_in = 16'sd1; @(posedge clk); x_in = 16'sd0;   // impulse
        // y pipeline: d[0] captures at impulse edge; y valid 2 edges later
        @(posedge clk);
        for (k=0; k<10; k=k+1) begin
            @(posedge clk); #1;
            if (y_out !== expected[k]) begin
                $display("FAIL index=%0d expected=%0d got=%0d", k, expected[k], y_out);
                errors = errors + 1;
            end
        end
        if (errors==0) $display("TEST PASSED"); else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end
endmodule
