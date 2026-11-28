`timescale 1ns/1ps
// Independent checker for the 16-tap symmetric FIR stream. It keeps its own
// accepted history and evaluates the filter in direct form (sixteen products,
// no pre-adder), models the five elastic slots abstractly, checks ready, valid
// and data before and after every rising edge, and schedules stimulus from its
// own model only, so a stuck DUT still reaches a verdict.
module fir16_sym_core_tb;
    reg clk=0, rst=1, in_valid=0, out_ready=0;
    reg signed [15:0] in_sample=0;
    wire in_ready, out_valid;
    wire signed [15:0] out_sample;
    fir16_sym_core dut(.clk(clk),.rst(rst),.in_sample(in_sample),.in_valid(in_valid),.in_ready(in_ready),
        .out_sample(out_sample),.out_valid(out_valid),.out_ready(out_ready));
    always #5 clk=~clk;

    // Reference state: slot valid bits and results, accepted history.
    reg s1=0, s2=0, s3=0, s4=0, s5=0;
    reg [15:0] d1=0, d2=0, d3=0, d4=0, d5=0, result=0;
    reg r1=0, r2=0, r3=0, r4=0, r5=0, push=0, pop=0, blocked=0, started=0, last_push=0;
    reg signed [15:0] held=0;
    integer hist [0:15];
    integer acc, rounded, k, nonzero;
    integer cycle=0, errors=0, accepted=0, retired=0, aborted=0;
    integer pos_sat=0, neg_sat=0, ties=0, full_stalls=0, collapses=0, replaces=0;
    integer history_resets=0, pulses=0, noise=0, extreme_acc=0;
    integer i, j;
    reg [31:0] seed=32'h3c6ef372;

    task fail;
        input [511:0] rule;
        begin
            errors=errors+1;
            if(errors<=40) $display("FAIL BEHAVIOR rule=%0s cycle=%0d",rule,cycle);
        end
    endtask
    task checker_fail;
        input [511:0] rule;
        begin errors=errors+1; $display("CHECKER_FAIL rule=%0s cycle=%0d",rule,cycle); end
    endtask
    task coverage_fail;
        input [511:0] rule;
        begin errors=errors+1; $display("COVERAGE_FAIL rule=%0s",rule); end
    endtask

    function [31:0] advance;
        input [31:0] value;
        reg [31:0] x;
        begin x=value^(value<<13); x=x^(x>>17); advance=x^(x<<5); end
    endfunction

    function integer coef;
        input integer index;
        integer m;
        begin
            m=(index<8) ? index : 15-index;
            case(m)
                0: coef=-6;
                1: coef=-20;
                2: coef=-24;
                3: coef=18;
                4: coef=110;
                5: coef=226;
                6: coef=330;
                default: coef=390;
            endcase
        end
    endfunction

    task check_ports;
        begin
            if(in_ready !== (!(s1 && s2 && s3 && s4 && s5) || out_ready)) fail("in_ready_elastic_bubble_collapse");
            if(out_valid !== s5) fail("out_valid_slot5_occupancy");
            if(s5 && out_sample !== d5) fail("rounded_saturated_result_or_stall_hold");
        end
    endtask

    // One clock cycle. Inputs change at the falling edge; ports are checked
    // before the rising edge and after its updates. A blocked sample is held
    // unchanged until accepted, except that reset aborts it.
    task step;
        input reset_now, offer;
        input integer value;
        input ready_now;
        begin
            @(negedge clk);
            rst=reset_now; out_ready=ready_now;
            if(blocked && !reset_now) begin in_valid=1; in_sample=held; end
            else begin in_valid=offer; in_sample=value; end
            #1; if(started) check_ports;
            @(posedge clk);
            cycle=cycle+1;
            r5=!s5 || out_ready; r4=!s4 || r5; r3=!s3 || r4; r2=!s2 || r3; r1=!s1 || r2;
            push=!rst && in_valid && r1;
            pop=!rst && s5 && out_ready;
            blocked=!rst && in_valid && !r1;
            held=in_sample;
            last_push=push;
            if(rst) begin
                nonzero=0;
                for(k=0;k<16;k=k+1) if(hist[k]!=0) nonzero=1;
                if(nonzero) history_resets=history_resets+1;
                aborted=aborted+s1+s2+s3+s4+s5;
                s1=0; s2=0; s3=0; s4=0; s5=0;
                for(k=0;k<16;k=k+1) hist[k]=0;
            end else begin
                if(s1 && s2 && s3 && s4 && s5 && !out_ready && in_valid) full_stalls=full_stalls+1;
                if(!r5 && ((r4 && s3) || (r3 && s2) || (r2 && s1) || push)) collapses=collapses+1;
                if(!in_valid && r1) noise=noise+1;
                if(push && pop && s1 && s2 && s3 && s4 && s5) replaces=replaces+1;
                if(pop) retired=retired+1;
                if(push) begin
                    for(k=15;k>0;k=k-1) hist[k]=hist[k-1];
                    hist[0]=in_sample; // signed: sign-extends into the integer
                    acc=0;
                    for(k=0;k<16;k=k+1) acc=acc+coef(k)*hist[k];
                    if(acc>70000000 || acc< -70000000) extreme_acc=extreme_acc+1;
                    if(((acc+1024) & 2047)==0) ties=ties+1;
                    rounded=(acc+1024)>>>11;
                    if(rounded>32767) begin result=16'h7fff; pos_sat=pos_sat+1; end
                    else if(rounded< -32768) begin result=16'h8000; neg_sat=neg_sat+1; end
                    else result=rounded[15:0];
                    accepted=accepted+1;
                end
                // Descending updates consume the OLD predecessor slots.
                if(r5) begin s5=s4; if(s4) d5=d4; end
                if(r4) begin s4=s3; if(s3) d4=d3; end
                if(r3) begin s3=s2; if(s2) d3=d2; end
                if(r2) begin s2=s1; if(s1) d2=d1; end
                if(r1) begin s1=in_valid; if(push) d1=result; end
            end
            if(accepted != retired+aborted+s1+s2+s3+s4+s5) checker_fail("transaction_conservation");
            #1; started=1; check_ports;
        end
    endtask

    // Called one ns after a rising edge: the pulse ends before the next one.
    task pulse_reset;
        begin
            #1 rst=1;
            #1 check_ports;
            #1 rst=0;
            #0.5 check_ports;
            pulses=pulses+1;
        end
    endtask

    // One accepted impulse followed by eighteen accepted zeros at full rate.
    task impulse;
        input integer value;
        integer n;
        begin
            step(0,1,value,1);
            for(n=0;n<18;n=n+1) step(0,1,0,1);
        end
    endtask

    initial begin
        for(k=0;k<16;k=k+1) hist[k]=0;
        step(1,0,0,0);
        step(1,1,1234,1); // reset dominates an offered sample
        // A: impulse responses of both signs; 512 and -512 make every odd
        // half-coefficient an exact rounding tie.
        impulse(32767); impulse(-32768); impulse(512); impulse(-512); impulse(1); impulse(-1);
        // B: constant extremes: the pre-adder sums need 17 bits, both rails saturate.
        for(i=0;i<40;i=i+1) step(0,1,32767,1);
        for(i=0;i<40;i=i+1) step(0,1,-32768,1);
        // C: windows aligned with the coefficient signs reach |acc| maximum.
        for(j=0;j<4;j=j+1)
            for(i=0;i<16;i=i+1) step(0,1,((((i<=2)||(i>=13)) ? 1 : 0) ^ (j%2)) ? -32768 : 32767,1);
        // D: alternating extremes at full rate.
        for(i=0;i<48;i=i+1) step(0,1,(i%2) ? -32768 : 32767,1);
        // E: fill all five slots behind a stalled output, hold a blocked
        // sample for five cycles, then drain with changing invalid data.
        for(i=0;i<10;i=i+1) step(0,1,i*3001-15000,0);
        if(!(s1 && s2 && s3 && s4 && s5) || !blocked) checker_fail("full_stall_setup");
        for(i=0;i<8;i=i+1) step(0,0,i*777-3000,1);
        // F: sparse input behind an intermittently stalled output: bubbles
        // must collapse toward the output.
        for(i=0;i<90;i=i+1) step(0,(i%3)==0,i*1103-30000,(i%7)>=4);
        for(i=0;i<8;i=i+1) step(0,0,0,1);
        // G: synchronous reset with nonzero history and a partly full
        // pipeline; the following impulse must see an all-zero history.
        for(i=0;i<3;i=i+1) step(0,1,20000-i*9000,0);
        step(1,1,555,0);
        for(i=0;i<20;i=i+1) step(0,1,(i==0) ? 16384 : 0,1);
        // H: off-edge reset pulses with a full stalled pipeline, nonzero
        // history and a blocked sample; nothing may change.
        for(i=0;i<7;i=i+1) step(0,1,i*4111-12000,0);
        if(!(s1 && s2 && s3 && s4 && s5) || !blocked) checker_fail("pulse_setup");
        pulse_reset;
        step(0,1,0,0); pulse_reset;
        for(i=0;i<12;i=i+1) step(0,1,i*97,1);
        // I: seeded random traffic with extremes, stalls and two resets.
        for(i=0;i<2000;i=i+1) begin
            seed=advance(seed);
            step(i==700 || i==1500, seed[1:0]!=2'b00,
                 (seed[6:5]==2'b00) ? (seed[7] ? 32767 : -32768) : $signed(seed[31:16]),
                 (i%64)<40 ? (seed[4:2]!=3'b000) : (seed[4:2]==3'b000));
        end
        for(i=0;i<12;i=i+1) step(0,0,0,1);
        if(s1 || s2 || s3 || s4 || s5 || accepted != retired+aborted) checker_fail("final_drain");
        if(pos_sat<10 || neg_sat<10 || ties<8 || extreme_acc<4) coverage_fail("arithmetic_corners");
        if(full_stalls<40 || collapses<100 || replaces<150 || noise<200) coverage_fail("flow_control");
        if(history_resets<3 || pulses!=2 || aborted<5) coverage_fail("resets");
        $display("COVERAGE cycles=%0d accepted=%0d retired=%0d aborted=%0d pos_sat=%0d neg_sat=%0d ties=%0d extreme=%0d full_stalls=%0d collapses=%0d replaces=%0d noise=%0d history_resets=%0d pulses=%0d",
            cycle,accepted,retired,aborted,pos_sat,neg_sat,ties,extreme_acc,full_stalls,collapses,replaces,noise,history_resets,pulses);
        if(errors==0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors",errors);
        $finish;
    end
    initial begin
        #1000000;
        $display("TEST FAILED: watchdog timeout");
        $finish;
    end
endmodule
