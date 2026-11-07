`timescale 1ns/1ps
// Black-box temporal model: exact countdown plus /,% transaction oracle.
// This checks behavior and timing; it does not prove iterative architecture.
module iterative_divider_case #(
    parameter WIDTH=8, USE_TOP=0, CASE_ID=0
)(input clk, output reg finished=0, output reg failed=0);
    reg rst=1, in_valid=0, out_ready=0;
    reg [WIDTH-1:0] dividend=0, divisor=0;
    wire in_ready, out_valid;
    wire [WIDTH-1:0] quotient, remainder;
    generate
        if (USE_TOP) begin: default_wrapper
            iterative_divider dut(.clk(clk), .rst(rst), .dividend(dividend),
                .divisor(divisor), .in_valid(in_valid), .in_ready(in_ready),
                .quotient(quotient), .remainder(remainder),
                .out_valid(out_valid), .out_ready(out_ready));
        end else begin: parameter_child
            iterative_divider_core #(.WIDTH(WIDTH)) dut(.clk(clk), .rst(rst),
                .dividend(dividend), .divisor(divisor),
                .in_valid(in_valid), .in_ready(in_ready),
                .quotient(quotient), .remainder(remainder),
                .out_valid(out_valid), .out_ready(out_ready));
        end
    endgenerate

    localparam [WIDTH-1:0] MAX_VALUE={WIDTH{1'b1}};
    reg [WIDTH-1:0] expected_quotient=0, expected_remainder=0;
    reg result_pending=0, model_started=0, last_accept=0;
    integer remaining_steps=0, accepted_at=0;
    integer checked=0, errors=0, accepted=0, retired=0, discarded=0;
    integer available_results=0, stalled_results=0, busy_cycles=0;
    integer blocked_busy=0, blocked_result=0, retirement_bubbles=0;
    integer zero_divisors=0, zero_dividends=0, reset_compute=0, reset_result=0;
    integer reset_stalled_result=0;
    integer reset_phases=0, exhaustive_pairs=0, directed_pairs=0, random_pairs=0;
    integer a, b, i, phase, n;
    reg [31:0] seed=32'h6d2b79f5 ^ CASE_ID;
    reg pending_valid=0;
    reg [WIDTH-1:0] pending_dividend=0, pending_divisor=0;
    reg push, pop;

    task fail;
        input [639:0] message;
        begin
            errors=errors+1;
            if (errors<=12)
                $display("FAIL case=%0d WIDTH=%0d cycle=%0d remaining=%0d pending=%0d: %0s",
                    CASE_ID,WIDTH,checked,remaining_steps,result_pending,message);
        end
    endtask

    task check_outputs;
        begin
            if (in_ready !== ((remaining_steps==0)&&!result_pending))
                fail("single outstanding readiness / retirement-edge bubble");
            if (out_valid !== result_pending)
                fail("exact WIDTH-step result availability / no early or late valid");
            if (result_pending) begin
                if (quotient !== expected_quotient) fail("unsigned quotient / stable held result");
                if (remainder !== expected_remainder) fail("unsigned remainder / stable held result");
            end
        end
    endtask

    task step;
        input reset_value, valid_value;
        input [WIDTH-1:0] dividend_value, divisor_value;
        input ready_value;
        begin
            @(negedge clk);
            rst=reset_value;
            in_valid=valid_value;
            dividend=dividend_value;
            divisor=divisor_value;
            out_ready=ready_value;
            #1;
            // Catch asynchronous reset or combinational early responses.
            if (model_started) check_outputs;
            @(posedge clk);
            if (model_started) check_outputs;
            push=in_valid&&(remaining_steps==0)&&!result_pending;
            pop=result_pending&&out_ready;
            last_accept=0;
            if (rst) begin
                if (remaining_steps>0) reset_compute=reset_compute+1;
                if (result_pending) reset_result=reset_result+1;
                if (result_pending&&!out_ready) reset_stalled_result=reset_stalled_result+1;
                if ((remaining_steps>0)||result_pending) discarded=discarded+1;
                remaining_steps=0;
                result_pending=0;
            end else begin
                busy_cycles=busy_cycles+(remaining_steps>0);
                blocked_busy=blocked_busy+((remaining_steps>0)&&in_valid);
                blocked_result=blocked_result+(result_pending&&in_valid&&!out_ready);
                stalled_results=stalled_results+(result_pending&&!out_ready);
                retirement_bubbles=retirement_bubbles+(pop&&in_valid&&!push);
                if (pop) begin
                    if (checked-accepted_at<WIDTH+1) fail("accepted transfer age below WIDTH+1");
                    result_pending=0;
                    retired=retired+1;
                end
                // A capture does not also perform a computation step.
                if (remaining_steps>0) begin
                    remaining_steps=remaining_steps-1;
                    if (remaining_steps==0) begin
                        result_pending=1;
                        available_results=available_results+1;
                    end
                end
                if (push) begin
                    if (divisor_value==0) begin
                        expected_quotient=MAX_VALUE;
                        expected_remainder=dividend_value;
                        zero_divisors=zero_divisors+1;
                    end else begin
                        expected_quotient=dividend_value/divisor_value;
                        expected_remainder=dividend_value%divisor_value;
                    end
                    zero_dividends=zero_dividends+(dividend_value==0);
                    remaining_steps=WIDTH;
                    accepted_at=checked;
                    accepted=accepted+1;
                    last_accept=1;
                end
            end
            #1;
            model_started=1;
            check_outputs;
            checked=checked+1;
            #1;
        end
    endtask

    function [31:0] advance;
        input [31:0] value;
        reg [31:0] x;
        begin
            x=value^(value<<13);
            x=x^(x>>17);
            advance=x^(x<<5);
        end
    endfunction

    // Idle input operands may change after capture, including during a held
    // result. They are deliberately unrelated to the captured operation.
    task finish_transaction;
        input integer stall_count;
        integer t;
        begin
            while (remaining_steps>0) begin
                seed=advance(seed);
                step(0,0,seed[WIDTH-1:0],~seed[WIDTH-1:0],1);
            end
            for (t=0; t<stall_count; t=t+1) begin
                seed=advance(seed);
                step(0,0,seed[WIDTH-1:0],~seed[WIDTH-1:0],0);
            end
            step(0,0,0,0,1);
        end
    endtask

    task transaction;
        input [WIDTH-1:0] av, bv;
        input integer stall_count;
        begin
            step(0,1,av,bv,1);
            if (!last_accept) fail("directed request not accepted from idle");
            finish_transaction(stall_count);
        end
    endtask

    initial begin
        step(1,0,0,0,0);
        step(1,0,0,0,0);
        // Exhaustive unsigned pairs, including zero, at every selected small width.
        if (WIDTH<=4) begin
            for (a=0; a<(1<<WIDTH); a=a+1)
                for (b=0; b<(1<<WIDTH); b=b+1) begin
                    transaction(a,b,(a+b)%3);
                    exhaustive_pairs=exhaustive_pairs+1;
                end
        end
        transaction(0,0,3);
        transaction(0,MAX_VALUE,2);
        transaction(MAX_VALUE,0,4);
        transaction(MAX_VALUE,1,2);
        transaction(MAX_VALUE,MAX_VALUE,3);
        transaction(1,MAX_VALUE,1);
        transaction(MAX_VALUE-1,MAX_VALUE,2);
        directed_pairs=7;
        for (i=0; i<WIDTH; i=i+1) begin
            // Powers of two, near powers, high bits, exact division and a<b.
            transaction(1<<i,1,1);
            transaction(MAX_VALUE,1<<i,2);
            transaction((1<<i)-1,1<<i,1);
            transaction(1<<i,(1<<i)+1,2);
            directed_pairs=directed_pairs+4;
            if (i<WIDTH-1) begin
                transaction(3<<i,1<<i,2);
                directed_pairs=directed_pairs+1;
            end
        end

        // A second request remains legally asserted throughout computation,
        // held result, and the first result's retirement edge. It is accepted
        // only on the following idle edge, with its original operands intact.
        step(0,1,MAX_VALUE,1,0);
        if (!last_accept) fail("first burst request not accepted");
        repeat (WIDTH) step(0,1,1,MAX_VALUE,0);
        repeat (4) step(0,1,1,MAX_VALUE,0);
        step(0,1,1,MAX_VALUE,1);
        if (last_accept) fail("new request accepted on result retirement edge");
        step(0,1,1,MAX_VALUE,1);
        if (!last_accept) fail("held second request not accepted on next idle edge");
        finish_transaction(3);

        // Reset before each computation phase, including the final step;
        // phase WIDTH resets a result already made visible. Reset dominates
        // asserted input and ready, and aborts pending work without an output.
        for (phase=0; phase<=WIDTH; phase=phase+1) begin
            step(0,1,MAX_VALUE,MAX_VALUE,0);
            if (!last_accept) fail("reset-phase request not accepted");
            for (n=0; n<phase; n=n+1) step(0,0,0,1,0);
            step(1,1,1,0,1);
            reset_phases=reset_phases+1;
            step(0,0,0,0,1);
        end
        // Reset a HELD result with ready low. Normal retirement cannot mask
        // an ignored reset. The second pending input is held unchanged until
        // reset aborts it; no result from either operation may later reappear.
        step(0,1,MAX_VALUE,1,0);
        if (!last_accept) fail("stalled-result reset request not accepted");
        repeat (WIDTH) step(0,1,1,MAX_VALUE,0);
        repeat (2) step(0,1,1,MAX_VALUE,0);
        step(1,1,1,MAX_VALUE,0);
        step(0,0,0,0,1);
        repeat (WIDTH+2) step(0,0,MAX_VALUE,0,1);
        // Idle reset with valid/ready asserted must not capture a new operation.
        step(1,1,MAX_VALUE,0,1);
        step(0,0,0,0,1);

        // Bounded deterministic randomized legal producer. Once asserted, the
        // pending tuple remains unchanged until capture; resets may abort it.
        for (i=0; i<1400; i=i+1) begin
            seed=advance(seed);
            if (!pending_valid || last_accept) begin
                pending_valid=seed[0]||seed[4];
                pending_dividend=seed[WIDTH-1:0];
                seed=advance(seed);
                pending_divisor=seed[WIDTH-1:0];
            end
            step(0,pending_valid,pending_dividend,pending_divisor,seed[2]||seed[7]);
            if (last_accept) random_pairs=random_pairs+1;
        end
        if (pending_valid&&!last_accept) begin
            while (!last_accept) step(0,1,pending_dividend,pending_divisor,1);
            random_pairs=random_pairs+1;
        end
        if (remaining_steps>0 || result_pending) finish_transaction(2);
        repeat (3) step(0,0,MAX_VALUE,0,1);
        if (remaining_steps!=0 || result_pending || accepted!=retired+discarded)
            fail("final drain / accepted-retired-discarded conservation");
        if (accepted<50 || retired<40 || busy_cycles<WIDTH*30 ||
            stalled_results<15 || blocked_busy<WIDTH || blocked_result<4 ||
            retirement_bubbles<1 || zero_divisors<2 || zero_dividends<2 ||
            reset_compute<WIDTH || reset_result<1 || reset_stalled_result<1 ||
            reset_phases!=WIDTH+1 ||
            directed_pairs!=6+5*WIDTH || random_pairs<40 ||
            ((WIDTH<=4)&&(exhaustive_pairs!=(1<<(2*WIDTH)))))
            fail("required arithmetic / temporal / reset coverage missing");
        $display("COVERAGE case=%0d WIDTH=%0d checked=%0d accepted=%0d retired=%0d discarded=%0d available=%0d busy=%0d stalled=%0d blocked_busy=%0d blocked_result=%0d retirement_bubbles=%0d div0=%0d zero_dividend=%0d reset_compute=%0d reset_result=%0d reset_stalled_result=%0d reset_phases=%0d exhaustive=%0d directed=%0d random=%0d",
            CASE_ID,WIDTH,checked,accepted,retired,discarded,available_results,
            busy_cycles,stalled_results,blocked_busy,blocked_result,retirement_bubbles,
            zero_divisors,zero_dividends,reset_compute,reset_result,reset_stalled_result,reset_phases,
            exhaustive_pairs,directed_pairs,random_pairs);
        failed=(errors!=0);
        finished=1;
    end
endmodule

module iterative_divider_tb;
    reg clk=0;
    wire [5:0] finished, failed;
    always #5 clk=~clk;
    iterative_divider_case #(.WIDTH(8),.USE_TOP(1),.CASE_ID(0)) default_case(clk,finished[0],failed[0]);
    iterative_divider_case #(.WIDTH(1),.CASE_ID(1)) width1_case(clk,finished[1],failed[1]);
    iterative_divider_case #(.WIDTH(2),.CASE_ID(2)) width2_case(clk,finished[2],failed[2]);
    iterative_divider_case #(.WIDTH(4),.CASE_ID(3)) width4_case(clk,finished[3],failed[3]);
    iterative_divider_case #(.WIDTH(13),.CASE_ID(4)) width13_case(clk,finished[4],failed[4]);
    iterative_divider_case #(.WIDTH(16),.CASE_ID(5)) width16_case(clk,finished[5],failed[5]);
    initial begin
        wait (&finished);
        #1;
        if (failed===6'b000000) $display("TEST PASSED");
        else $display("TEST FAILED: iterative divider matrix failed mask=%b",failed);
        $finish;
    end
    initial begin
        #200000;
        $display("TEST FAILED: iterative divider matrix watchdog");
        $finish;
    end
endmodule
