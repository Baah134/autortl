`timescale 1ns/1ps
module dot4_pipeline_tb;
    reg clk=0, rst=1;
    reg [7:0] a0=0,b0=0,a1=0,b1=0,a2=0,b2=0,a3=0,b3=0;
    wire [17:0] dot_result;
    dot4_pipeline dut(.clk(clk),.rst(rst),.a0(a0),.b0(b0),.a1(a1),.b1(b1),
        .a2(a2),.b2(b2),.a3(a3),.b3(b3),.dot_result(dot_result));
    // Probe the merge's complete declared domain, beyond reachable pair sums.
    reg merge_rst=1;
    reg [16:0] merge_left=0, merge_right=0;
    wire [17:0] merge_result;
    dot4_merge merge_probe(.clk(clk),.rst(merge_rst),.left_sum(merge_left),
        .right_sum(merge_right),.dot_result(merge_result));
    reg [17:0] pending_dot=0, expected_dot=0;
    reg started=0, merge_done=0, pipeline_done=0;
    integer errors=0, checked=0, reset_checks=0, held_checks=0, pulse_checks=0;
    integer i, term;
    reg [63:0] vector_value, seed=64'h3141592653589793;
    always #5 clk=~clk;
    task fail;
        input [511:0] message;
        begin
            errors=errors+1;
            if(errors<=12) $display("FAIL cycle=%0d: %0s",checked,message);
        end
    endtask
    function [17:0] arithmetic;
        input [63:0] value;
        integer t;
        reg [31:0] total, left_operand, right_operand;
        begin
            total=0;
            for(t=0;t<4;t=t+1) begin
                left_operand=(value >> (56-16*t)) & 255;
                right_operand=(value >> (48-16*t)) & 255;
                total=total+left_operand*right_operand;
            end
            arithmetic=total[17:0];
        end
    endfunction
    task step;
        input reset_value;
        input [63:0] value;
        begin
            @(negedge clk);
            rst=reset_value;
            {a0,b0,a1,b1,a2,b2,a3,b3}=value;
            #1;
            if(started) begin
                held_checks=held_checks+1;
                if(dot_result !== expected_dot) fail("output changed away from active edge");
            end
            @(posedge clk);
            if(rst) begin
                expected_dot=0; pending_dot=0; reset_checks=reset_checks+1;
            end else begin
                expected_dot=pending_dot;
                pending_dot=arithmetic(value);
            end
            #1; started=1; checked=checked+1;
            if(dot_result !== expected_dot) fail("unsigned arithmetic/order/two-edge latency/reset");
            #1;
        end
    endtask
    task short_reset_pulse;
        begin
            // Called two ns after a rising edge; no rising edge sees this pulse.
            rst=1; #1;
            if(dot_result !== expected_dot) fail("asynchronous top reset response");
            rst=0; #1;
            if(dot_result !== expected_dot) fail("off-edge reset output hold");
            pulse_checks=pulse_checks+1;
            // Next step verifies the stored partial sums survived the pulse.
        end
    endtask
    task merge_step;
        input reset_value;
        input [16:0] left_value,right_value;
        reg [17:0] old_result, expected_result;
        begin
            @(negedge clk);
            old_result=merge_result;
            merge_rst=reset_value; merge_left=left_value; merge_right=right_value;
            expected_result=reset_value ? 18'd0 : ({1'b0,left_value}+{1'b0,right_value});
            #1;
            if(merge_result !== old_result) fail("merge probe changed off edge");
            @(posedge clk); #1;
            if(merge_result !== expected_result) fail("merge full 17-bit input domain");
        end
    endtask
    initial begin
        step(1,0); step(1,0);
        step(0,0); step(0,64'hffffffffffffffff);
        step(0,64'hffffffffffffffff); step(0,0);
        // Isolate every product; then vary left and right halves independently.
        for(term=0;term<4;term=term+1) begin
            vector_value=64'hffff << (48-16*term);
            step(0,vector_value); step(0,0);
        end
        step(0,64'hffff010100000000); // pair carry 65026
        step(0,64'hffffffff00000000); // pair carry above bit15
        step(0,64'hffffffffffffffff); // final carry above bit16
        step(0,64'h8001ff02037f0481);
        step(0,64'h0102030405060708);
        step(0,64'hf1e2d3c4b5a69788);
        for(i=0;i<256;i=i+1) begin
            vector_value={i[7:0],8'hff,8'h81,i[7:0],8'h03,8'h7f,i[7:0],8'hc5};
            step(0,vector_value);
        end
        step(0,64'hffffffffffffffff);
        step(0,64'hffffffffffffffff);
        short_reset_pulse;
        step(0,64'h0101010101010101);
        // Clear occupied stages, then verify the first released edge is zero.
        step(1,64'hffffffffffffffff);
        step(0,64'h0102030405060708);
        step(0,64'hffffffffffffffff);
        for(i=0;i<400;i=i+1) begin
            seed=seed^(seed<<13); seed=seed^(seed>>7); seed=seed^(seed<<17);
            step((i==131)||(i==317),seed);
        end
        step(0,0); step(0,0); step(0,0);
        if(checked<680 || held_checks<675 || reset_checks<5 || pulse_checks!=1)
            fail("required scenario coverage missing");
        $display("COVERAGE checked=%0d holds=%0d resets=%0d pulses=%0d",checked,held_checks,reset_checks,pulse_checks);
        pipeline_done=1;
    end
    initial begin
        repeat(2) @(posedge clk);
        #1;
        if(merge_result !== 0) fail("merge probe initial reset");
        merge_step(0,17'd131071,17'd131071);
        merge_step(0,17'd65535,17'd1);
        merge_step(0,17'd65536,17'd65536);
        merge_step(0,17'd1,17'd131071);
        merge_step(1,17'd131071,17'd131071);
        merge_step(0,0,0);
        merge_done=1;
    end
    initial begin
        wait(pipeline_done && merge_done); #1;
        if(errors==0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d assertions",errors);
        $finish;
    end
    initial begin
        #15000;
        $display("TEST FAILED: watchdog");
        $finish;
    end
endmodule
