`timescale 1ns/1ps
module elastic_dot4_tb;
    reg clk=0,rst=1,in_valid=0,out_ready=0;
    reg [7:0] a0=0,b0=0,a1=0,b1=0,a2=0,b2=0,a3=0,b3=0;
    wire in_ready,out_valid;
    wire [17:0] out_data;
    elastic_dot4 dut(.clk(clk),.rst(rst),.a0(a0),.b0(b0),.a1(a1),.b1(b1),
        .a2(a2),.b2(b2),.a3(a3),.b3(b3),.in_valid(in_valid),.in_ready(in_ready),
        .out_data(out_data),.out_valid(out_valid),.out_ready(out_ready));
    always #5 clk=~clk;
    // Independent slots hold whole mathematical results, not DUT partial sums.
    reg slot1_valid=0,slot2_valid=0,started=0;
    reg [17:0] slot1_value=0,slot2_value=0;
    reg [17:0] queue [0:4095];
    integer capture_cycle [0:4095];
    integer head=0,tail=0,accepted=0,retired=0,discarded=0,cycle=0,errors=0;
    integer stage1_resets=0,stage2_resets=0,both_resets=0,stalled_resets=0;
    integer full_stalls=0,full_replacements=0,bubbles=0,offedge_pulses=0;
    integer steady_count=0,steady_best=0,stage1_pulses=0,both_pulses=0,i,term;
    reg ready1,ready2,push,pop;
    reg producer_blocked=0;
    reg [63:0] held_operands=0,vector_value,seed=64'h243f6a8885a308d3;
    task behavior_fail;
        input [639:0] message;
        begin
            errors=errors+1;
            if(errors<=15) $display("BEHAVIOR_FAIL rule=%0s cycle=%0d slots=%b%b queue=%0d",
                message,cycle,slot2_valid,slot1_valid,tail-head);
        end
    endtask
    task checker_fail;
        input [639:0] message;
        begin
            errors=errors+1;
            $display("CHECKER_FAIL rule=%0s cycle=%0d",message,cycle);
        end
    endtask
    task coverage_fail;
        input [639:0] message;
        begin
            errors=errors+1;
            $display("COVERAGE_FAIL rule=%0s cycle=%0d",message,cycle);
        end
    endtask
    function [17:0] arithmetic;
        input [63:0] value;
        integer t;
        reg [31:0] total,lhs,rhs;
        begin
            total=0;
            for(t=0;t<4;t=t+1) begin
                lhs=(value>>(56-16*t)) & 255;
                rhs=(value>>(48-16*t)) & 255;
                total=total+lhs*rhs;
            end
            arithmetic=total[17:0];
        end
    endfunction
    task check_outputs;
        begin
            if(out_valid !== slot2_valid) behavior_fail("exact stage2 availability/validity");
            if(in_ready !== (!slot1_valid || !slot2_valid || out_ready))
                behavior_fail("exact readiness/capacity/downstream propagation");
            if(slot2_valid && out_data !== slot2_value)
                behavior_fail("arithmetic/captured tuple/stalled output stability");
            if(slot2_valid) begin
                if(head>=tail) behavior_fail("output with no outstanding transaction");
                else if(out_data !== queue[head]) behavior_fail("queue order/multiplicity");
            end
        end
    endtask
    task step;
        input reset_value,offer;
        input [63:0] offered_operands;
        input ready_value;
        begin
            @(negedge clk);
            rst=reset_value; out_ready=ready_value;
            // A blocked producer holds its ENTIRE tuple using actual acceptance.
            if(producer_blocked && !reset_value) begin
                in_valid=1;
                {a0,b0,a1,b1,a2,b2,a3,b3}=held_operands;
            end else begin
                in_valid=offer;
                {a0,b0,a1,b1,a2,b2,a3,b3}=offered_operands;
            end
            #1;
            if(started) check_outputs;
            @(posedge clk);
            if(started) check_outputs; // old values, before DUT NBA
            ready2=!slot2_valid || out_ready;
            ready1=!slot1_valid || ready2;
            push=in_valid && ready1;
            pop=slot2_valid && out_ready;
            producer_blocked=!rst && in_valid && (in_ready !== 1'b1);
            held_operands={a0,b0,a1,b1,a2,b2,a3,b3};
            if(rst) begin
                stage1_resets=stage1_resets+(slot1_valid&&!slot2_valid);
                stage2_resets=stage2_resets+(!slot1_valid&&slot2_valid);
                both_resets=both_resets+(slot1_valid&&slot2_valid);
                stalled_resets=stalled_resets+(slot2_valid&&!out_ready);
                discarded=discarded+(tail-head);
                head=tail;
                slot1_valid=0;slot2_valid=0;steady_count=0;
            end else begin
                full_stalls=full_stalls+(slot1_valid&&slot2_valid&&!out_ready);
                full_replacements=full_replacements+(slot1_valid&&slot2_valid&&push&&pop);
                bubbles=bubbles+!in_valid;
                if(push&&pop) steady_count=steady_count+1;
                else steady_count=0;
                if(steady_count>steady_best) steady_best=steady_count;
                if(pop) begin
                    if(head>=tail) checker_fail("retirement without accepted input");
                    else begin
                        if(cycle-capture_cycle[head]<2) checker_fail("minimum accepted transfer age2");
                        head=head+1;retired=retired+1;
                    end
                end
                if(push) begin
                    if(tail>=4096) checker_fail("reference queue capacity exhausted");
                    else begin
                        queue[tail]=arithmetic({a0,b0,a1,b1,a2,b2,a3,b3});
                        capture_cycle[tail]=cycle;
                        tail=tail+1;accepted=accepted+1;
                    end
                end
                // Move old slot1 before replacing it; no combinational bypass.
                if(ready2) begin
                    slot2_valid=slot1_valid;
                    if(slot1_valid) slot2_value=slot1_value;
                end
                if(ready1) begin
                    slot1_valid=in_valid;
                    if(in_valid) slot1_value=arithmetic({a0,b0,a1,b1,a2,b2,a3,b3});
                end
            end
            if(tail-head != ((slot1_valid ? 1 : 0)+(slot2_valid ? 1 : 0))) checker_fail("slot/queue occupancy disagreement");
            if(tail-head>2 || tail<head) checker_fail("reference capacity bounds");
            if(accepted!=retired+discarded+tail-head) checker_fail("transaction conservation");
            #1;started=1;check_outputs;
            cycle=cycle+1;#1;
        end
    endtask
    task pulse_reset;
        begin
            // Called at posedge+2ns; pulse ends at +4ns, before next edge.
            stage1_pulses=stage1_pulses+(slot1_valid&&!slot2_valid);
            both_pulses=both_pulses+(slot1_valid&&slot2_valid);
            rst=1;#1;check_outputs;
            rst=0;#1;check_outputs;
            offedge_pulses=offedge_pulses+1;
        end
    endtask
    initial begin
        step(1,0,0,0);step(1,0,0,0);
        // Reset each occupancy independently, with outstanding nonzero values.
        step(0,1,64'hffffffffffffffff,0);
        step(1,1,64'h0101010101010101,0); // stage1 only
        step(0,1,64'hffffffffffffffff,0);
        step(0,0,0,0);
        step(1,1,64'h0202020202020202,0); // stage2 only, stalled
        step(0,1,64'hffffffffffffffff,0);
        step(0,1,64'h0102030405060708,0);
        step(1,1,64'h0303030303030303,0); // both slots, stalled
        step(0,1,64'hffffffffffffffff,0);
        pulse_reset; // stage1-only pulse: later stage2 result must survive
        step(0,0,0,0);
        repeat(4) step(0,0,0,1);
        step(0,1,64'hffffffffffffffff,0);
        step(0,1,64'h1122334455667788,0);
        pulse_reset; // both slots must survive; test again at subsequent edges
        repeat(8) step(0,1,64'hdeadbeef01234567,0);
        for(i=0;i<40;i=i+1) step(0,1,i+1,1);
        repeat(5) step(0,0,0,1);
        // Individual product terms and unsigned/carry extrema.
        for(term=0;term<4;term=term+1) begin
            vector_value=64'hffff << (48-16*term);
            step(0,1,vector_value,1);
            step(0,1,0,1);
        end
        step(0,1,64'hffffffffffffffff,1);
        step(0,1,64'hffffffffffffffff,1); // repeated result, distinct transaction
        step(0,1,64'hffffffff00000000,1);
        step(0,1,64'h8001ff02037f0481,1);
        for(i=0;i<256;i=i+1) begin
            vector_value={i[7:0],8'hff,8'h81,i[7:0],8'h03,8'h7f,i[7:0],8'hc5};
            step(0,1,vector_value,1);
        end
        repeat(5) step(0,0,0,1);
        for(i=0;i<500;i=i+1) begin
            seed=seed^(seed<<13);seed=seed^(seed>>7);seed=seed^(seed<<17);
            step((i==131)||(i==317),seed[0]||seed[3],seed,seed[2]||seed[7]);
        end
        // Preserve any blocked producer before draining with no new offers.
        repeat(8) step(0,0,0,1);
        if(head!=tail || slot1_valid || slot2_valid) checker_fail("final drain");
        if(accepted!=retired+discarded) checker_fail("final conservation");
        if(cycle<830 || accepted<300 || retired<290 || full_stalls<8 ||
           full_replacements<30 || steady_best<30 || bubbles<10 ||
           stage1_resets<1 || stage2_resets<1 || both_resets<1 ||
           stalled_resets<2 || offedge_pulses!=2 || stage1_pulses!=1 || both_pulses!=1) coverage_fail("required scenario coverage missing");
        $display("COVERAGE cycles=%0d accepted=%0d retired=%0d discarded=%0d fullstall=%0d replacement=%0d steady=%0d bubbles=%0d reset1=%0d reset2=%0d resetboth=%0d resetstall=%0d pulses=%0d pulse1=%0d pulseboth=%0d",
            cycle,accepted,retired,discarded,full_stalls,full_replacements,steady_best,bubbles,
            stage1_resets,stage2_resets,both_resets,stalled_resets,offedge_pulses,stage1_pulses,both_pulses);
        if(errors==0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d assertions",errors);
        $finish;
    end
    initial begin
        #20000;
        $display("TEST FAILED: watchdog");
        $finish;
    end
endmodule
