`timescale 1ns/1ps
// Independent cycle-exact checker for uart_fifo (8N1 UART transmitter fed by a
// byte FIFO). Each case owns a reference model of spec.md (waiting-byte queue,
// frame timer) and checks in_ready and tx before and after every rising edge.
// A separate UART receiver samples tx at bit centres and compares each frame
// with an expected-byte queue of accepted bytes. No DUT internals are read;
// stimulus follows the model, never DUT outputs, so a stuck DUT still ends.
module uart_fifo_case #(parameter CPB=16, parameter USE_TOP=1, parameter DEPTH=8,
                        parameter RAND_N=150, parameter CASE_ID=0)(
    input clk, output reg finished=0, output reg failed=0, output reg [31:0] error_count=0);
    reg rst=1, in_valid=0;
    reg [7:0] in_data=0;
    wire in_ready, tx;
    generate
        if (USE_TOP) begin: default_top
            uart_fifo dut(.clk(clk),.rst(rst),.in_data(in_data),.in_valid(in_valid),
                .in_ready(in_ready),.tx(tx));
        end else begin: parameter_child
            uart_tx #(.CLKS_PER_BIT(CPB)) dut(.clk(clk),.rst(rst),.tx_data(in_data),
                .tx_valid(in_valid),.tx_ready(in_ready),.tx(tx));
        end
    endgenerate

    localparam FRAME = 10*CPB;
    // Reference model. m_t counts rising edges since the current frame started;
    // m_q holds the waiting bytes (top only; the child has no FIFO).
    reg m_busy=0;
    integer m_t=0, m_count=0;
    reg [7:0] m_cur=0;
    reg [7:0] m_q [0:15];
    // Expected-byte scoreboard (accepted, not yet received) and receiver.
    reg [7:0] sb [0:31];
    integer sb_head=0, sb_n=0;
    reg rx_active=0;
    integer rx_t=0, rx_bit=0;
    reg [7:0] rx_byte=0;
    reg started=0, ending=0, free=0, acc=0, st=0, last_accept=0, exp_tx=1, exp_ready=1, v=0;
    integer bitn=0, i, n, p, guard, mode;
    integer checked=0, errors=0, accepted=0, received=0, flushed=0, frames=0, aborted=0;
    integer back_to_back=0, idle_starts=0, full_cycles=0, blocked=0, joint=0;
    integer pulses=0, directed=0, random_bytes=0;
    reg [31:0] seed=32'h1f2e3d4c ^ CASE_ID;

    task fail;
        input [511:0] rule;
        begin
            errors=errors+1;
            if(errors<=12) $display("FAIL BEHAVIOR case=%0d CPB=%0d step=%0d t=%0d rule=%0s",CASE_ID,CPB,checked,m_t,rule);
        end
    endtask
    task checker_fail;
        input [511:0] rule;
        begin errors=errors+1; $display("CHECKER_FAIL case=%0d CPB=%0d step=%0d rule=%0s",CASE_ID,CPB,checked,rule); end
    endtask
    task coverage_fail;
        input [511:0] rule;
        begin errors=errors+1; $display("COVERAGE_FAIL case=%0d CPB=%0d rule=%0s",CASE_ID,CPB,rule); end
    endtask

    function [31:0] advance;
        input [31:0] value;
        reg [31:0] x;
        begin x=value^(value<<13); x=x^(x>>17); advance=x^(x<<5); end
    endfunction

    task check_outputs;
        begin
            if(m_busy) begin
                bitn=m_t/CPB;                 // frame bit 0 start, 1..8 data, 9 stop
                if(bitn==0) exp_tx=1'b0;
                else if(bitn<=8) exp_tx=m_cur[bitn-1];
                else exp_tx=1'b1;
            end else exp_tx=1'b1;
            if(USE_TOP) exp_ready=(m_count<DEPTH);
            else exp_ready=!m_busy || (m_t==FRAME-1);
            if(in_ready !== exp_ready) begin
                if(USE_TOP) fail("in_ready_exactly_when_fewer_than_depth_waiting");
                else fail("tx_ready_idle_or_last_stop_cycle");
            end
            if(tx !== exp_tx) begin
                if(!m_busy) fail("tx_idle_high");
                else if(bitn==0) fail("tx_start_bit");
                else if(bitn<=8) fail("tx_data_bit_lsb_first");
                else fail("tx_stop_bit");
            end
        end
    endtask

    // UART receiver: detects the falling start edge, samples at bit centres.
    task receive;
        begin
            if(rx_active) begin
                rx_t=rx_t+1;
                if((rx_t%CPB)==CPB/2) begin
                    rx_bit=rx_t/CPB;
                    if(rx_bit==0) begin
                        if(tx !== 1'b0) fail("rx_start_bit_centre");
                    end else if(rx_bit<=8) begin
                        rx_byte[rx_bit-1]=tx;
                    end else begin
                        if(tx !== 1'b1) fail("rx_stop_bit_centre");
                        if(sb_n==0) fail("rx_frame_without_accepted_byte");
                        else begin
                            if(rx_byte !== sb[sb_head]) fail("rx_byte_value_or_order");
                            sb_head=(sb_head+1)%32; sb_n=sb_n-1;
                        end
                        received=received+1;
                        rx_active=0;
                    end
                end
            end else if(tx === 1'b0) begin
                rx_active=1; rx_t=0;
            end
        end
    endtask

    // One clock cycle: inputs change at the falling edge; ports are checked
    // before the rising edge and after its updates.
    task step;
        input reset_value, valid_value;
        input [7:0] data_value;
        begin
            @(negedge clk);
            rst=reset_value; in_valid=valid_value; in_data=data_value;
            #1; if(started) check_outputs;
            @(posedge clk);
            ending=m_busy && (m_t==FRAME-1);
            free=!m_busy || ending;
            if(USE_TOP) begin
                acc=!rst && in_valid && (m_count<DEPTH);
                st=!rst && free && (m_count>0);
            end else begin
                acc=!rst && in_valid && free;
                st=acc;
            end
            last_accept=acc;
            if(rst) begin
                if(m_busy) aborted=aborted+1;
                flushed=flushed+sb_n;
                m_busy=0; m_t=0; m_count=0;
                sb_n=0; rx_active=0;
            end else begin
                if(in_valid && !acc) blocked=blocked+1;
                if(USE_TOP && m_count==DEPTH) full_cycles=full_cycles+1;
                if(st) begin
                    if(USE_TOP) begin
                        m_cur=m_q[0];
                        for(i=0;i<15;i=i+1) m_q[i]=m_q[i+1];
                        m_count=m_count-1;
                        if(acc) joint=joint+1;
                    end else m_cur=in_data;
                    if(ending) back_to_back=back_to_back+1;
                    else idle_starts=idle_starts+1;
                    m_busy=1; m_t=0; frames=frames+1;
                end else if(ending) m_busy=0;
                else if(m_busy) m_t=m_t+1;
                if(acc) begin
                    if(USE_TOP) begin m_q[m_count]=in_data; m_count=m_count+1; end
                    if(sb_n>=32) checker_fail("scoreboard_overflow");
                    else begin sb[(sb_head+sb_n)%32]=in_data; sb_n=sb_n+1; end
                    accepted=accepted+1;
                end
            end
            #1; started=1; check_outputs; if(!rst) receive; checked=checked+1;
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

    // Offer a byte and hold it until the model accepts it.
    task offer;
        input [7:0] d;
        begin
            step(0,1,d);
            while(!last_accept) step(0,1,d);
        end
    endtask

    // Idle (in_valid low, noise on in_data) until nothing is waiting or sent.
    task drain;
        begin
            while(m_busy || m_count>0) begin seed=advance(seed); step(0,0,seed[7:0]); end
            seed=advance(seed); step(0,0,seed[7:0]);
        end
    endtask

    initial begin
        step(1,0,8'h00);
        step(1,1,8'h81); // reset dominates an offered byte
        step(1,1,8'h7e);
        // Directed single bytes into an empty, idle design.
        offer(8'ha5); drain;
        offer(8'h00); drain;
        offer(8'hff); drain;
        offer(8'h01); drain;
        offer(8'h80); drain;
        offer(8'h5a); drain;
        directed=6;
        // Back-to-back burst, each byte held until accepted.
        for(n=0;n<5;n=n+1) offer(8'h30+n*17);
        drain;
        // Fill to full while the source keeps offering: in_ready stays low until
        // each frame start (top) or the last stop-bit cycle (child).
        for(n=0;n<DEPTH+6;n=n+1) offer(8'hc3^(n*37));
        drain;
        // Synchronous reset at every frame phase, with bytes waiting (top) or
        // offered (child) and a byte offered at the reset edge.
        for(p=0;p<FRAME;p=p+1) begin
            offer(p^8'h96);
            if(USE_TOP) step(0,1,p^8'h3c); // first frame starts, a second byte is accepted
            if(!m_busy || m_t!=0) checker_fail("reset_phase_setup");
            n=0;
            while(m_t!=p) begin step(0,1,8'h40+n*7); n=n+1; end
            step(1,1,8'ha5);
            step(0,0,8'h00);
        end
        // Off-edge reset pulses during frames, with bytes waiting, and idle.
        offer(8'h00);
        if(USE_TOP) begin offer(8'h00); offer(8'hff); end
        while(m_busy || m_count>0) begin
            seed=advance(seed);
            step(0,0,seed[7:0]);
            if((m_t%(2*CPB+1))==3) pulse_reset;
        end
        step(0,0,8'h00); pulse_reset;
        step(0,0,8'h00);
        // Seeded random bursts: dense, sparse, idle and half-rate phases; the
        // source may drop in_valid without a transfer. One synchronous reset.
        guard=0; mode=0;
        while(random_bytes<RAND_N && guard<RAND_N*FRAME*4) begin
            seed=advance(seed);
            if(seed[7:0]<8'd5) mode=seed[9:8];
            case(mode)
                0: v=(seed[12:10]!=3'd0);
                1: v=(seed[13:10]==4'd0);
                2: v=1'b0;
                default: v=seed[10];
            endcase
            step(guard==(RAND_N*FRAME/3)+7,v,seed[23:16]);
            if(last_accept) random_bytes=random_bytes+1;
            guard=guard+1;
        end
        drain;
        if(m_busy || m_count!=0) checker_fail("final_model_idle");
        if(sb_n!=0 || rx_active || accepted!=received+flushed)
            fail("every_accepted_byte_received_once_in_order");
        if(directed!=6 || random_bytes<RAND_N || aborted<FRAME || pulses<4 || back_to_back<4 ||
           idle_starts<FRAME || blocked<FRAME ||
           (USE_TOP && (full_cycles<FRAME || joint<FRAME || flushed<2*FRAME)))
            coverage_fail("required_frame_reset_full_coverage");
        $display("COVERAGE case=%0d CPB=%0d steps=%0d accepted=%0d received=%0d flushed=%0d frames=%0d aborted=%0d back_to_back=%0d idle_starts=%0d full=%0d blocked=%0d joint=%0d pulses=%0d random=%0d",
            CASE_ID,CPB,checked,accepted,received,flushed,frames,aborted,back_to_back,idle_starts,full_cycles,blocked,joint,pulses,random_bytes);
        error_count=errors;
        failed=(errors!=0);
        finished=1;
    end
endmodule

module uart_fifo_tb;
    reg clk=0;
    wire [3:0] finished, failed;
    wire [31:0] errors0, errors1, errors2, errors3;
    always #5 clk=~clk;
    uart_fifo_case #(.CPB(16),.USE_TOP(1),.DEPTH(8),.RAND_N(150),.CASE_ID(0)) top_case(clk,finished[0],failed[0],errors0);
    uart_fifo_case #(.CPB(2),.USE_TOP(0),.DEPTH(0),.RAND_N(60),.CASE_ID(1)) cpb2_case(clk,finished[1],failed[1],errors1);
    uart_fifo_case #(.CPB(3),.USE_TOP(0),.DEPTH(0),.RAND_N(60),.CASE_ID(2)) cpb3_case(clk,finished[2],failed[2],errors2);
    uart_fifo_case #(.CPB(7),.USE_TOP(0),.DEPTH(0),.RAND_N(60),.CASE_ID(3)) cpb7_case(clk,finished[3],failed[3],errors3);
    initial begin
        wait(&finished);
        #1;
        if(failed===4'b0000) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors",errors0+errors1+errors2+errors3);
        $finish;
    end
    initial begin
        #3000000;
        $display("TEST FAILED: watchdog timeout");
        $finish;
    end
endmodule
