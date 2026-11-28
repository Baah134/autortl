`timescale 1ns/1ps
// Independent cycle-exact checker for the UART receiver + FIFO + error counter
// hierarchy. Each case keeps its own model of the synchronized line, the frame
// offsets and votes, the FIFO queue and the saturating counters, drives rx and
// out_ready from its own schedule (never from DUT outputs) and checks every
// output port before and after each rising edge. No DUT internals are read.
module uart_rx_fifo_case #(parameter D=2, parameter A=2, parameter USE_TOP=0, parameter CASE_ID=0)(
    input clk, output reg finished=0, output reg failed=0, output reg [31:0] error_count=0);
    localparam BITC = 16*D;        // clk cycles per bit
    localparam DECIDE = 153*D;     // frame offset of the stop-bit decision
    localparam DEPTH = 1<<A;
    reg rst=1, rx=1, out_ready=0;
    wire [7:0] out_data;
    wire out_valid, frame_err;
    wire [3:0] ferr_count, ovf_count;
    generate
        if (USE_TOP) begin: default_top
            uart_rx_fifo dut(.clk(clk),.rst(rst),.rx(rx),.out_data(out_data),.out_valid(out_valid),
                .out_ready(out_ready),.frame_err(frame_err),.ferr_count(ferr_count),.ovf_count(ovf_count));
        end else begin: parameter_children
            wire strobe, overflow;
            wire [7:0] received;
            uart_rx_core #(.OVERSAMPLE_DIV(D)) rx_unit(.clk(clk),.rst(rst),.rx(rx),.rx_data(received),
                .rx_strobe(strobe),.frame_err(frame_err));
            rx_fifo #(.ADDR_BITS(A)) fifo_unit(.clk(clk),.rst(rst),.wr_en(strobe),.wr_data(received),
                .out_data(out_data),.out_valid(out_valid),.out_ready(out_ready),.overflow(overflow));
            rx_err_count count_unit(.clk(clk),.rst(rst),.ferr_in(frame_err),.ovf_in(overflow),
                .ferr_count(ferr_count),.ovf_count(ovf_count));
        end
    endgenerate

    // Reference model. line1/line2 hold rx as driven one and two edges back.
    reg line1=1, line2=1, line=1, vote=0;
    reg m_busy=0, m_wait=0, m_strobe=0, m_ferr=0, m_ovf=0;
    reg new_strobe=0, new_ferr=0, pop=0, push=0;
    reg [7:0] m_byte=0, m_bits=0;
    reg [2:0] m_votes=0;
    reg [3:0] m_fcnt=0, m_ocnt=0;
    reg [7:0] fifo_q [0:15];
    integer head=0, tail=0, m_e0=0, off=0, bitn=0, ph=0;
    // Frames the stimulus intends, checked when the model decides them.
    reg [9:0] expect_q [0:63];
    integer exp_head=0, exp_tail=0;
    reg started=0;
    integer ready_mode=0, cycle=0, errors=0;
    integer good=0, framing=0, false_starts=0, overflows=0, full_replace=0, ferr_saturated=0;
    integer ovf_saturated=0, noisy_frames=0, tight_frames=0, sync_resets=0, busy_resets=0, pulses=0;
    integer i, n, guard;
    reg [31:0] seed=32'h6b8b4567 ^ (CASE_ID*32'h9e3779b9);

    task fail;
        input [511:0] rule;
        begin
            errors=errors+1;
            if(errors<=12) $display("FAIL BEHAVIOR case=%0d D=%0d A=%0d cycle=%0d rule=%0s",CASE_ID,D,A,cycle,rule);
        end
    endtask
    task checker_fail;
        input [511:0] rule;
        begin errors=errors+1; $display("CHECKER_FAIL case=%0d D=%0d cycle=%0d rule=%0s",CASE_ID,D,cycle,rule); end
    endtask
    task coverage_fail;
        input [511:0] rule;
        begin errors=errors+1; $display("COVERAGE_FAIL case=%0d D=%0d A=%0d rule=%0s",CASE_ID,D,A,rule); end
    endtask

    function [31:0] advance;
        input [31:0] value;
        reg [31:0] x;
        begin x=value^(value<<13); x=x^(x>>17); advance=x^(x<<5); end
    endfunction

    task check_outputs;
        begin
            if(out_valid !== (tail!=head)) fail("fifo_out_valid_occupancy");
            if(out_data !== ((tail!=head) ? fifo_q[head%16] : 8'd0)) fail("fifo_head_byte_or_zero_when_empty");
            if(frame_err !== m_ferr) fail("frame_err_one_cycle_pulse");
            if(ferr_count !== m_fcnt) fail("saturating_frame_error_count");
            if(ovf_count !== m_ocnt) fail("saturating_overflow_count");
        end
    endtask

    task expect_frame;
        input [1:0] kind;    // 1 good byte, 2 framing error
        input [7:0] value;
        begin expect_q[exp_tail%64]={kind,value}; exp_tail=exp_tail+1; end
    endtask

    task decided;
        input [1:0] kind;
        input [7:0] value;
        begin
            if(exp_head==exp_tail) checker_fail("unexpected_frame_decision");
            else begin
                if(expect_q[exp_head%64] !== {kind,value}) checker_fail("frame_decision_model");
                exp_head=exp_head+1;
            end
        end
    endtask

    // One clock cycle: inputs change at the falling edge; ports are checked
    // before the rising edge and after its updates.
    task step;
        input reset_value, rx_value;
        begin
            @(negedge clk);
            rst=reset_value; rx=rx_value;
            seed=advance(seed);
            if(ready_mode==0) out_ready=1;
            else if(ready_mode==1) out_ready=0;
            else if(ready_mode==2) out_ready=seed[7]^seed[19];
            else out_ready=m_strobe; // pop exactly when a received byte is being written
            #1; if(started) check_outputs;
            @(posedge clk);
            cycle=cycle+1;
            if(rst) begin
                if(m_busy) busy_resets=busy_resets+1;
                sync_resets=sync_resets+1;
                line1=1; line2=1; m_busy=0; m_wait=0; m_strobe=0; m_ferr=0; m_ovf=0;
                m_byte=0; head=tail; m_fcnt=0; m_ocnt=0; exp_head=exp_tail;
            end else begin
                // Counters take the pulses registered at the previous edge.
                if(m_ferr && m_fcnt==15) ferr_saturated=ferr_saturated+1;
                if(m_ovf && m_ocnt==15) ovf_saturated=ovf_saturated+1;
                if(m_ferr && m_fcnt!=15) m_fcnt=m_fcnt+1;
                if(m_ovf && m_ocnt!=15) m_ocnt=m_ocnt+1;
                // FIFO: the receiver's previous-edge strobe is the write request.
                pop=out_ready && (tail!=head);
                push=m_strobe && ((tail-head)<DEPTH || pop);
                if(push && pop && (tail-head)==DEPTH) full_replace=full_replace+1;
                if(pop) head=head+1;
                if(push) begin fifo_q[tail%16]=m_byte; tail=tail+1; end
                m_ovf=m_strobe && !push;
                if(m_ovf) overflows=overflows+1;
                // Receiver: line is rx as driven two edges before this one.
                line=line2; new_strobe=0; new_ferr=0;
                if(!m_busy) begin
                    if(m_wait) begin
                        if(line) m_wait=0;
                    end else if(!line) begin
                        m_busy=1; m_e0=cycle;
                    end
                end else begin
                    off=cycle-m_e0; bitn=off/BITC; ph=off%BITC;
                    if(ph==7*D) m_votes[0]=line;
                    if(ph==8*D) m_votes[1]=line;
                    if(ph==9*D) begin
                        m_votes[2]=line;
                        vote=(m_votes[0]+m_votes[1]+m_votes[2])>=2;
                        if(bitn==0) begin
                            if(vote) begin m_busy=0; false_starts=false_starts+1; end
                        end else if(bitn<=8) begin
                            m_bits[bitn-1]=vote;
                        end else begin
                            m_busy=0;
                            if(vote) begin
                                new_strobe=1; m_byte=m_bits; good=good+1; decided(1,m_bits);
                            end else begin
                                new_ferr=1; m_wait=1; framing=framing+1; decided(2,8'h00);
                            end
                        end
                    end
                end
                m_strobe=new_strobe; m_ferr=new_ferr;
                line2=line1; line1=rx;
            end
            #1; started=1; check_outputs;
        end
    endtask

    // Called one ns after a rising edge: the pulse ends before the next one.
    task pulse_reset;
        begin
            #1 rst=1;
            #1 check_outputs;
            #1 rst=0;
            #0.5 check_outputs;
            pulses=pulses+1;
        end
    endtask

    task idle;
        input integer count;
        integer k;
        begin for(k=0;k<count;k=k+1) step(0,1); end
    endtask

    // Drive one 8N1 frame from offset 0 (the first low cycle); the model must
    // be able to detect it. Noisy frames carry random values at every offset
    // the receiver ignores (1..DECIDE except the vote offsets) and invert at
    // most one of the three votes of each bit. After the stop decision a good
    // frame idles high; a framing error stays low to the end of the stop bit.
    // gap: high cycles afterwards. event_at: frame offset of an off-edge reset
    // pulse (kind 0) or of a synchronous reset that aborts the frame (kind 1).
    task send_frame;
        input [7:0] value;
        input stop_value, noisy;
        input integer gap, event_at, event_kind;
        integer q, b, p;
        reg nominal, v, aborted;
        reg [1:0] corrupt;
        begin
            expect_frame(stop_value ? 2'd1 : 2'd2, stop_value ? value : 8'h00);
            if(noisy) noisy_frames=noisy_frames+1;
            if(gap==0) tight_frames=tight_frames+1;
            aborted=0; corrupt=3; q=0;
            while(q<=DECIDE && !aborted) begin
                b=q/BITC; p=q%BITC;
                if(b==0) nominal=0; else if(b<=8) nominal=value[b-1]; else nominal=stop_value;
                if(p==0) begin seed=advance(seed); corrupt=seed[13:12]; end // 3: no vote inverted
                v=nominal;
                if(noisy && q>0) begin
                    if(p==7*D) begin if(corrupt==0) v=!nominal; end
                    else if(p==8*D) begin if(corrupt==1) v=!nominal; end
                    else if(p==9*D) begin if(corrupt==2) v=!nominal; end
                    else begin seed=advance(seed); v=seed[3]; end
                end
                if(q==event_at && event_kind==1) begin
                    step(1,1); aborted=1;
                end else begin
                    step(0,v);
                    if(q==event_at && event_kind==0) pulse_reset;
                end
                q=q+1;
            end
            if(aborted) idle(gap);
            else begin
                if(!stop_value) for(q=DECIDE+1;q<10*BITC;q=q+1) step(0,0);
                idle(gap);
            end
        end
    endtask

    // Low for len cycles, then high for after cycles. The caller states the
    // decision the receiver must reach (0 none, 1 byte 0xFF, 2 framing error).
    task low_pulse;
        input integer len, after;
        input [1:0] outcome;
        integer k;
        begin
            if(outcome!=0) expect_frame(outcome, outcome==1 ? 8'hff : 8'h00);
            for(k=0;k<len;k=k+1) step(0,0);
            idle(after);
        end
    endtask

    initial begin
        step(1,1);
        step(1,0); // reset dominates; the synchronizer restarts high
        idle(5);
        // 1: clean frames with a full stop bit.
        ready_mode=0;
        send_frame(8'h00,1,0,7*D-1,-1,0); send_frame(8'hff,1,0,7*D-1,-1,0);
        send_frame(8'h01,1,0,7*D-1,-1,0); send_frame(8'h80,1,0,7*D-1,-1,0);
        send_frame(8'h5a,1,0,7*D-1,-1,0); send_frame(8'hc3,1,0,7*D+3,-1,0);
        // 2: back-to-back frames at the minimum spacing (start right after the
        // stop decision), consumer stalled for part of it.
        ready_mode=2;
        for(i=0;i<4;i=i+1) send_frame(8'h96+i*8'h11,1,0,0,-1,0);
        ready_mode=0; idle(3);
        // 3: noisy frames: anything at ignored offsets, one bad vote per bit.
        for(i=0;i<10;i=i+1) begin seed=advance(seed); send_frame(seed[27:20],1,1,i%3,-1,0); end
        // 4: start-bit validation: glitches with at most one low vote, each
        // followed by the earliest legal restart; then a start with two low
        // votes, which is a real frame of all ones.
        low_pulse(1,9*D,0); send_frame(8'h3c,1,0,2,-1,0);
        low_pulse(7*D,2*D+1,0); send_frame(8'hc5,1,1,2,-1,0);
        low_pulse(8*D,D+1,0); send_frame(8'h69,1,0,2,-1,0);
        low_pulse(8*D+1,DECIDE-8*D,1);
        low_pulse(2,40,0);
        // 5: framing errors: stop bit low, earliest restart after the line
        // returns high, and two long breaks that report exactly one error.
        send_frame(8'h55,0,0,1,-1,0); send_frame(8'h0f,1,0,3,-1,0);
        send_frame(8'hf0,0,1,1,-1,0); send_frame(8'he1,1,0,3,-1,0);
        low_pulse(3*BITC*10+5,1,2); send_frame(8'h2d,1,0,3,-1,0);
        low_pulse(DECIDE+1,BITC,2);
        // 6: FIFO: fill with the consumer stalled, then pop exactly at the
        // write edges of a full FIFO (no overflow), then overflow, then drain.
        ready_mode=1;
        for(i=0;i<DEPTH;i=i+1) send_frame(8'h10+i,1,0,0,-1,0);
        idle(4);
        ready_mode=3;
        for(i=0;i<3;i=i+1) send_frame(8'h40+i,1,0,0,-1,0);
        idle(4);
        ready_mode=1;
        for(i=0;i<3;i=i+1) send_frame(8'h70+i,1,0,0,-1,0);
        idle(4);
        ready_mode=2; idle(6);
        ready_mode=0; idle(DEPTH+2);
        // 7: synchronous resets: mid-frame with a nonempty FIFO and nonzero
        // counters, then while waiting for the line after a framing error.
        ready_mode=1;
        send_frame(8'h21,1,0,0,-1,0);
        send_frame(8'h55,0,0,1,-1,0);
        send_frame(8'h42,1,0,0,5*BITC+3,1);
        idle(4);
        if(m_busy || tail!=head || m_fcnt!=0) checker_fail("reset_setup");
        send_frame(8'h24,1,0,0,-1,0);
        low_pulse(DECIDE+20,0,2);
        step(1,0);
        idle(3);
        send_frame(8'h81,1,0,3,-1,0);
        // 8: off-edge reset pulses mid-frame and with a held FIFO entry.
        send_frame(8'h99,1,0,2,3*BITC+5,0);
        send_frame(8'h18,1,1,2,DECIDE-1,0);
        idle(2); pulse_reset; idle(2);
        ready_mode=0; idle(4);
        // 9: saturate both counters (16 or more events each).
        for(i=0;i<18;i=i+1) send_frame(8'h00,0,i%2,1,-1,0);
        ready_mode=1;
        for(i=0;i<DEPTH+20;i=i+1) send_frame(8'hc0+i,1,0,0,-1,0);
        ready_mode=0; idle(DEPTH+2);
        // 10: seeded random traffic: frames, noise, framing errors, glitches.
        ready_mode=2;
        guard=0;
        for(i=0;i<36;i=i+1) begin
            seed=advance(seed);
            n=seed[2:0];
            if(n==7) low_pulse(1+seed[10:8],9*D+seed[14:12],0);
            else if(n==6) send_frame(seed[23:16],0,seed[5],1+seed[7:6],-1,0);
            else send_frame(seed[23:16],1,seed[5],(seed[4] ? 0 : 7*D-1),-1,0);
        end
        ready_mode=0; idle(DEPTH+4);
        if(m_busy || m_wait || tail!=head || exp_head!=exp_tail) checker_fail("final_drain");
        if(good<70 || framing<24 || false_starts<4 || noisy_frames<12 || tight_frames<30)
            coverage_fail("frame_shapes");
        if(overflows<20 || full_replace<3 || ferr_saturated<2 || ovf_saturated<2)
            coverage_fail("fifo_and_counter_saturation");
        if(busy_resets<1 || sync_resets<4 || pulses<3) coverage_fail("resets");
        $display("COVERAGE case=%0d D=%0d A=%0d cycles=%0d good=%0d framing=%0d false_starts=%0d noisy=%0d tight=%0d overflows=%0d full_replace=%0d ferr_sat=%0d ovf_sat=%0d busy_resets=%0d resets=%0d pulses=%0d",
            CASE_ID,D,A,cycle,good,framing,false_starts,noisy_frames,tight_frames,overflows,full_replace,
            ferr_saturated,ovf_saturated,busy_resets,sync_resets,pulses);
        error_count=errors;
        failed=(errors!=0);
        finished=1;
    end
endmodule

module uart_rx_fifo_tb;
    reg clk=0;
    wire [2:0] finished, failed;
    wire [31:0] errors0, errors1, errors2;
    always #5 clk=~clk;
    uart_rx_fifo_case #(.D(2),.A(2),.USE_TOP(1),.CASE_ID(0)) default_case(clk,finished[0],failed[0],errors0);
    uart_rx_fifo_case #(.D(1),.A(3),.CASE_ID(1)) fast_deep_case(clk,finished[1],failed[1],errors1);
    uart_rx_fifo_case #(.D(3),.A(1),.CASE_ID(2)) slow_shallow_case(clk,finished[2],failed[2],errors2);
    initial begin
        wait(&finished);
        #1;
        if(failed===3'b000) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors",errors0+errors1+errors2);
        $finish;
    end
    initial begin
        #5000000;
        $display("TEST FAILED: watchdog timeout");
        $finish;
    end
endmodule
