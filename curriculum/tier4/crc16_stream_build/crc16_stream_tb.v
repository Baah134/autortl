`timescale 1ns/1ps
// Independent CRC-16/CCITT-FALSE stream checker. It keeps its own bit-serial
// reference model and an exact one-slot scoreboard, never reads DUT internals,
// and schedules stimulus from the model so a stuck DUT still reaches a verdict.
module crc16_stream_tb;
    reg clk=0, rst=1, in_valid=0, in_last=0, out_ready=0;
    reg [7:0] in_data=0;
    wire in_ready, out_valid, out_last;
    wire [15:0] out_crc;
    crc16_stream dut(.clk(clk),.rst(rst),.in_data(in_data),.in_last(in_last),
        .in_valid(in_valid),.in_ready(in_ready),.out_crc(out_crc),.out_last(out_last),
        .out_valid(out_valid),.out_ready(out_ready));
    always #5 clk=~clk;

    // Reference state: the single output slot plus the running frame CRC.
    reg slot_valid=0, slot_last=0;
    reg [15:0] slot_crc=0, frame_state=16'hffff, check_crc=0;
    integer frame_bytes=0;
    reg started=0, blocked=0, last_push=0, model_ready=0, push=0, pop=0;
    reg [7:0] held_data=0;
    reg held_last=0;
    integer cycle=0, errors=0, accepted=0, retired=0, aborted=0;
    integer frames=0, single_frames=0, long_frames=0, stalls=0, replaces=0;
    integer noise=0, blocked_cycles=0, mid_frame_resets=0, occupied_resets=0;
    integer check_frames=0, pulses=0, i;
    reg [31:0] seed=32'h1d872b41;

    task behavior_fail;
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

    // Bit-serial formulation (message bit XOR register MSB), deliberately not
    // the byte-XOR form used by typical RTL.
    function [15:0] crc_serial;
        input [15:0] state;
        input [7:0] value;
        integer k;
        reg [15:0] c;
        reg feedback;
        begin
            c=state;
            for(k=7;k>=0;k=k-1) begin
                feedback=c[15]^value[k];
                c={c[14:0],1'b0};
                if(feedback) c=c^16'h1021;
            end
            crc_serial=c;
        end
    endfunction

    function [31:0] advance;
        input [31:0] value;
        reg [31:0] x;
        begin x=value^(value<<13); x=x^(x>>17); advance=x^(x<<5); end
    endfunction

    task check_ports;
        begin
            if(in_ready !== (!slot_valid || out_ready)) behavior_fail("exact_in_ready");
            if(out_valid !== slot_valid) behavior_fail("exact_out_valid");
            if(slot_valid && out_crc !== slot_crc) behavior_fail("frame_crc_value_or_stall_hold");
            if(slot_valid && out_last !== slot_last) behavior_fail("last_flag_or_stall_hold");
        end
    endtask

    // One clock cycle. Inputs change at the falling edge; ports are checked
    // before the rising edge and after its nonblocking updates. A blocked byte
    // is held unchanged until accepted, except that reset aborts it.
    task step;
        input reset_now, offer;
        input [7:0] value;
        input last_value, ready_now;
        begin
            @(negedge clk);
            rst=reset_now; out_ready=ready_now;
            if(blocked && !reset_now) begin
                in_valid=1; in_data=held_data; in_last=held_last;
            end else begin
                in_valid=offer; in_data=value; in_last=last_value;
            end
            #1; if(started) check_ports;
            @(posedge clk);
            cycle=cycle+1;
            model_ready=!slot_valid || out_ready;
            push=!rst && in_valid && model_ready;
            pop=!rst && slot_valid && out_ready;
            blocked=!rst && in_valid && !model_ready;
            held_data=in_data; held_last=in_last;
            last_push=push;
            if(rst) begin
                if(slot_valid) begin occupied_resets=occupied_resets+1; aborted=aborted+1; end
                if(frame_bytes!=0) mid_frame_resets=mid_frame_resets+1;
                slot_valid=0; frame_state=16'hffff; frame_bytes=0;
            end else begin
                if(slot_valid && !out_ready) stalls=stalls+1;
                if(!in_valid) noise=noise+1;
                if(blocked) blocked_cycles=blocked_cycles+1;
                if(pop) retired=retired+1;
                if(push) begin
                    if(pop) replaces=replaces+1;
                    slot_crc=crc_serial(frame_state,in_data);
                    slot_last=in_last; slot_valid=1;
                    accepted=accepted+1; frame_bytes=frame_bytes+1;
                    if(in_last) begin
                        frames=frames+1;
                        if(frame_bytes==1) single_frames=single_frames+1;
                        if(frame_bytes>=16) long_frames=long_frames+1;
                        frame_state=16'hffff; frame_bytes=0;
                    end else frame_state=slot_crc;
                end else if(pop) slot_valid=0;
            end
            if(accepted != retired+aborted+slot_valid) checker_fail("transaction_conservation");
            #1; started=1; check_ports;
        end
    endtask

    // Offer one byte until the model accepts it. The consumer stalls for
    // `stall` cycles first, so the byte waits behind an occupied slot.
    task send_byte;
        input [7:0] value;
        input last_value;
        input integer stall;
        integer s;
        begin
            s=0;
            step(0,1,value,last_value,stall==0);
            while(!last_push) begin
                s=s+1;
                step(0,1,value,last_value,s>=stall);
            end
        end
    endtask

    task idle;
        input integer count;
        input ready_now;
        integer s;
        begin
            for(s=0;s<count;s=s+1) begin
                seed=advance(seed);
                step(0,0,seed[7:0],seed[8],ready_now); // invalid noise payload
            end
        end
    endtask

    task send_check_string;
        input integer stall;
        integer c;
        begin
            for(c=0;c<9;c=c+1) send_byte(8'h31+c,c==8,stall);
            if(!slot_valid || !slot_last || slot_crc !== 16'h29b1) checker_fail("check_frame_model");
            check_frames=check_frames+1;
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

    initial begin
        // The checker's own model must reproduce the published check value.
        check_crc=16'hffff;
        for(i=0;i<9;i=i+1) check_crc=crc_serial(check_crc,8'h31+i);
        if(check_crc !== 16'h29b1) checker_fail("reference_check_value");
        step(1,0,8'h00,0,0);
        step(1,1,8'h55,1,1); // reset dominates an offered byte
        // A: '123456789' at full rate.
        send_check_string(0);
        idle(2,1);
        // B: the same frame with stalls and invalid noise gaps between bytes.
        for(i=0;i<9;i=i+1) begin
            send_byte(8'h31+i,i==8,i%4);
            if(i==8) begin
                if(!slot_last || slot_crc !== 16'h29b1) checker_fail("check_frame_model");
                check_frames=check_frames+1;
            end
            idle(i%3,i%2);
        end
        idle(3,1);
        // C: single-byte frames at extreme byte values.
        send_byte(8'h00,1,0); send_byte(8'hff,1,1); send_byte(8'h80,1,2);
        send_byte(8'h01,1,0); send_byte(8'h7f,1,3); send_byte(8'hfe,1,1);
        idle(2,1);
        // D: one 40-byte frame at full rate (continuous retire and replace).
        for(i=0;i<40;i=i+1) send_byte(i*37+11,i==39,0);
        idle(2,1);
        // E: synchronous reset mid-frame with an occupied stalled slot and a
        // blocked byte. The next frame must restart from 0xFFFF.
        send_byte(8'h12,0,0); send_byte(8'h34,0,0);
        step(0,1,8'h56,0,0);
        if(!blocked || frame_bytes!=2) checker_fail("reset_setup");
        step(1,1,8'h56,0,0);
        send_check_string(1);
        idle(2,1);
        // F: off-edge reset pulses mid-frame, with an occupied stalled slot and
        // a blocked byte, then with a held result and with an empty slot.
        send_byte(8'hc3,0,0);
        step(0,1,8'h3c,1,0);
        pulse_reset;
        step(0,1,8'h3c,1,0);
        pulse_reset;
        if(!blocked || !slot_valid || frame_bytes!=1) checker_fail("pulse_setup");
        step(0,1,8'h3c,1,1);
        idle(1,0); pulse_reset;
        idle(1,1); pulse_reset;
        idle(1,1);
        // G: deterministic random traffic with two synchronous resets.
        for(i=0;i<1600;i=i+1) begin
            seed=advance(seed);
            step(i==411 || i==1203, seed[1:0]!=0, seed[15:8], seed[18:16]==0, seed[5:4]!=0);
        end
        // H: drain.
        idle(4,1);
        if(slot_valid || accepted != retired+aborted) checker_fail("final_drain");
        if(check_frames!=3) coverage_fail("check_frames");
        if(frames<70 || single_frames<10 || long_frames<2) coverage_fail("frame_shapes");
        if(stalls<150 || replaces<400 || noise<150 || blocked_cycles<150) coverage_fail("flow_control");
        if(mid_frame_resets<1 || occupied_resets<1 || pulses!=4) coverage_fail("reset_pulses");
        $display("COVERAGE cycles=%0d accepted=%0d retired=%0d aborted=%0d frames=%0d single=%0d long=%0d stalls=%0d replaces=%0d noise=%0d blocked=%0d mid_frame_resets=%0d occupied_resets=%0d pulses=%0d",
            cycle,accepted,retired,aborted,frames,single_frames,long_frames,stalls,replaces,noise,blocked_cycles,mid_frame_resets,occupied_resets,pulses);
        if(errors==0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors",errors);
        $finish;
    end
    initial begin
        #2000000;
        $display("TEST FAILED: watchdog timeout");
        $finish;
    end
endmodule
