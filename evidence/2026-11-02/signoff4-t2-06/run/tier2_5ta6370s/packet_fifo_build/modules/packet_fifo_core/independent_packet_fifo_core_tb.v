`timescale 1ns/1ps
// Independent accepted-transaction shift queue. No DUT internals are observed.
module packet_fifo_case #(
    parameter WIDTH=8, DEPTH=3, USE_TOP=0, CASE_ID=0
)(input clk, output reg finished=0, output reg failed=0);
    reg rst=1, in_valid=0, in_last=0, out_ready=0;
    reg [WIDTH-1:0] in_data=0;
    wire in_ready, out_valid, out_last;
    wire [WIDTH-1:0] out_data;
    generate
        if (USE_TOP) begin: default_wrapper
            packet_fifo_core dut(.clk(clk), .rst(rst), .in_data(in_data),
                .in_last(in_last), .in_valid(in_valid), .in_ready(in_ready),
                .out_data(out_data), .out_last(out_last),
                .out_valid(out_valid), .out_ready(out_ready));
        end else begin: parameter_child
            packet_fifo_core #(.WIDTH(WIDTH), .DEPTH(DEPTH)) dut(
                .clk(clk), .rst(rst), .in_data(in_data), .in_last(in_last),
                .in_valid(in_valid), .in_ready(in_ready), .out_data(out_data),
                .out_last(out_last), .out_valid(out_valid), .out_ready(out_ready));
        end
    endgenerate

    reg [WIDTH-1:0] expected_data [0:DEPTH-1];
    reg expected_last [0:DEPTH-1];
    integer accepted_cycle [0:DEPTH-1];
    integer queued=0, errors=0, checked=0;
    integer accepted=0, retired=0, discarded=0;
    integer accepted_markers=0, retired_markers=0, discarded_markers=0;
    integer full_cycles=0, stalled=0, simultaneous=0, full_simultaneous=0;
    integer boundary_simultaneous=0, full_boundary_simultaneous=0;
    integer ending_stalls=0, ordinary_stalls=0;
    integer idle_tag_changes=0, occupied_resets=0, marker_resets=0;
    integer empty_cycles=0, bubbles=0, max_queued=0, directed_packets=0;
    integer i, j, k, packet_length, shift_index;
    reg model_started=0, push, pop, last_push=0;
    reg pending_valid=0, pending_last=0, previous_idle_tag=0;
    reg [WIDTH-1:0] pending_data=0;
    reg [31:0] seed=32'h9e3779b9 ^ CASE_ID;

    task fail;
        input [639:0] message;
        begin
            errors=errors+1;
            if (errors<=12)
                $display("FAIL case=%0d WIDTH=%0d DEPTH=%0d cycle=%0d queued=%0d: %0s",
                    CASE_ID, WIDTH, DEPTH, checked, queued, message);
        end
    endtask

    task check_outputs;
        begin
            if (out_valid !== (queued!=0)) fail("nonempty validity / no empty bypass");
            if (in_ready !== ((queued<DEPTH)||out_ready))
                fail("exact capacity / full simultaneous readiness");
            if (queued>0) begin
                if (out_data !== expected_data[0]) fail("oldest full-width data / order / stall stability");
                if (out_last !== expected_last[0]) fail("oldest marker / tuple alignment / stall stability");
            end
        end
    endtask

    task step;
        input reset_value, valid_value;
        input [WIDTH-1:0] data_value;
        input last_value, ready_value;
        begin
            @(negedge clk);
            rst=reset_value;
            in_valid=valid_value;
            in_data=data_value;
            in_last=last_value;
            out_ready=ready_value;
            #1;
            // Synchronous reset must not erase the old tuple before capture.
            if (model_started) check_outputs;
            @(posedge clk);
            if (model_started) check_outputs;
            push=in_valid && ((queued<DEPTH)||out_ready);
            pop=(queued>0) && out_ready;
            last_push=0;
            if (rst) begin
                occupied_resets=occupied_resets+(queued>0);
                for (shift_index=0; shift_index<queued; shift_index=shift_index+1) begin
                    discarded_markers=discarded_markers+expected_last[shift_index];
                    marker_resets=marker_resets+expected_last[shift_index];
                end
                discarded=discarded+queued;
                queued=0;
            end else begin
                full_cycles=full_cycles+(queued==DEPTH);
                stalled=stalled+((queued>0)&&!out_ready);
                simultaneous=simultaneous+(push&&pop);
                full_simultaneous=full_simultaneous+((queued==DEPTH)&&push&&pop);
                if (queued>0) begin
                    ending_stalls=ending_stalls+(!out_ready&&expected_last[0]);
                    ordinary_stalls=ordinary_stalls+(!out_ready&&!expected_last[0]);
                    boundary_simultaneous=boundary_simultaneous+
                        (push&&pop&&(in_last!=expected_last[0]));
                    full_boundary_simultaneous=full_boundary_simultaneous+
                        ((queued==DEPTH)&&push&&pop&&(in_last!=expected_last[0]));
                    if (!in_valid&&!out_ready&&(in_last!=previous_idle_tag))
                        idle_tag_changes=idle_tag_changes+1;
                end
                previous_idle_tag=in_last;
                empty_cycles=empty_cycles+(queued==0);
                bubbles=bubbles+!in_valid;
                // Retire the OLD tuple, then append the accepted NEW tuple.
                if (pop) begin
                    if (checked-accepted_cycle[0]<1) fail("accepted transfer age below one");
                    retired_markers=retired_markers+expected_last[0];
                    for (shift_index=0; shift_index<DEPTH-1; shift_index=shift_index+1) begin
                        expected_data[shift_index]=expected_data[shift_index+1];
                        expected_last[shift_index]=expected_last[shift_index+1];
                        accepted_cycle[shift_index]=accepted_cycle[shift_index+1];
                    end
                    queued=queued-1;
                    retired=retired+1;
                end
                if (push) begin
                    expected_data[queued]=in_data;
                    expected_last[queued]=in_last;
                    accepted_cycle[queued]=checked;
                    queued=queued+1;
                    accepted=accepted+1;
                    accepted_markers=accepted_markers+in_last;
                    last_push=1;
                end
            end
            if (queued>max_queued) max_queued=queued;
            if (queued<0 || queued>DEPTH) fail("reference bounds");
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
    function [WIDTH-1:0] payload;
        input integer index;
        reg [31:0] value;
        begin
            value=(index*137)+(CASE_ID*53)+32'h1a35;
            payload=value;
        end
    endfunction

    initial begin
        step(1,0,0,0,0);
        step(1,0,0,0,0);
        // Exact capacity, blocked pending tuple, then OLD retirement / NEW capture.
        // Pending input stays identical throughout every blocked cycle.
        for (i=0; i<DEPTH; i=i+1) step(0,1,payload(i),i[0],0);
        repeat (6) step(0,1,{WIDTH{1'b1}},1,0);
        step(0,1,{WIDTH{1'b1}},1,1);
        for (i=0; i<4*DEPTH+8; i=i+1) step(0,1,payload(i+32),i[0],1);
        repeat (DEPTH+3) step(0,0,0,0,1);

        // Explicit marker and ordinary stalls. Idle in_last changes are legal
        // and must not leak into an already queued tuple (including DEPTH=1).
        for (j=0; j<2; j=j+1) begin
            step(0,1,payload(90),j[0],0);
            for (i=0; i<8; i=i+1) step(0,0,0,i[0],0);
            step(0,0,0,0,1);
        end

        // Consecutive packets, including packets longer than every FIFO depth.
        // Positions advance only after actual accepted input; ready=1 gives
        // one acceptance per call even when the FIFO begins full.
        for (j=0; j<6; j=j+1) begin
            case (j)
                0: packet_length=1;
                1: packet_length=2;
                2: packet_length=3;
                3: packet_length=4;
                4: packet_length=7;
                default: packet_length=17;
            endcase
            for (k=0; k<packet_length; k=k+1) begin
                step(0,1,payload(100+k+j*19),k==packet_length-1,1);
                if (!last_push) fail("directed packet input not accepted");
            end
            directed_packets=directed_packets+1;
        end
        // Same data with different tags; alternating markers and single beats.
        repeat (12) step(0,1,{WIDTH{1'b1}},1,1);
        for (i=0; i<32; i=i+1) step(0,1,{WIDTH{1'b1}},i[0],1);
        for (i=0; i<256; i=i+1) step(0,1,payload(i),((i%7)==6),1);
        step(0,1,(1 << (WIDTH-1))|1,0,1);
        repeat (DEPTH+3) step(0,0,0,0,1);

        // Abort an unfinished packet. Reset dominates even a would-be push/pop.
        for (i=0; i<DEPTH; i=i+1) step(0,1,payload(i+200),0,0);
        step(1,1,{WIDTH{1'b1}},1,1);
        step(0,0,0,1,1);
        // Flush queued endings too; no old marker may survive reset.
        for (i=0; i<DEPTH; i=i+1) step(0,1,payload(i+220),1,0);
        step(1,1,0,0,0);
        step(0,1,payload(240),0,0);
        repeat (DEPTH+3) step(0,0,0,1,1);

        // Legal producer: a pending valid tuple is held until accepted. Reset
        // may abort it and any partial packet; no manufactured ending is needed.
        for (i=0; i<500; i=i+1) begin
            seed=advance(seed);
            if (!pending_valid || last_push) begin
                pending_valid=seed[0]||seed[3];
                pending_data=seed[WIDTH-1:0];
                pending_last=seed[5];
            end
            step((i==131)||(i==317),pending_valid,pending_data,pending_last,seed[2]||seed[7]);
            if (i==131 || i==317) pending_valid=0;
        end
        if (pending_valid && !last_push) step(0,1,pending_data,pending_last,1);
        repeat (DEPTH+5) step(0,0,0,0,1);
        if (queued!=0 || accepted!=retired+discarded)
            fail("final drain / beat conservation");
        if (accepted_markers!=retired_markers+discarded_markers)
            fail("marker conservation");
        if (checked<850 || accepted<400 || retired<380 || max_queued!=DEPTH ||
            full_cycles<6 || stalled<20 || simultaneous<250 || full_simultaneous<1 ||
            boundary_simultaneous<5 || full_boundary_simultaneous<1 ||
            ending_stalls<8 || ordinary_stalls<8 ||
            idle_tag_changes<8 || empty_cycles<4 || bubbles<2 ||
            occupied_resets<2 || marker_resets<1 || directed_packets!=6)
            fail("required scenario coverage missing");
        $display("COVERAGE case=%0d WIDTH=%0d DEPTH=%0d checked=%0d accepted=%0d retired=%0d discarded=%0d accepted_markers=%0d retired_markers=%0d discarded_markers=%0d full=%0d stall=%0d simultaneous=%0d full_simultaneous=%0d boundary_simultaneous=%0d full_boundary_simultaneous=%0d ending_stalls=%0d ordinary_stalls=%0d idle_tag_changes=%0d resets=%0d marker_resets=%0d packets=%0d",
            CASE_ID,WIDTH,DEPTH,checked,accepted,retired,discarded,
            accepted_markers,retired_markers,discarded_markers,full_cycles,stalled,
            simultaneous,full_simultaneous,boundary_simultaneous,full_boundary_simultaneous,ending_stalls,
            ordinary_stalls,idle_tag_changes,occupied_resets,marker_resets,directed_packets);
        failed=(errors!=0);
        finished=1;
    end
endmodule

module packet_fifo_core_tb;
    reg clk=0;
    wire [5:0] finished, failed;
    always #5 clk=~clk;
    packet_fifo_case #(.WIDTH(8),.DEPTH(3),.USE_TOP(1),.CASE_ID(0)) default_case(clk,finished[0],failed[0]);
    packet_fifo_case #(.WIDTH(1),.DEPTH(1),.CASE_ID(1)) depth1_case(clk,finished[1],failed[1]);
    packet_fifo_case #(.WIDTH(8),.DEPTH(2),.CASE_ID(2)) depth2_case(clk,finished[2],failed[2]);
    packet_fifo_case #(.WIDTH(8),.DEPTH(4),.CASE_ID(3)) depth4_case(clk,finished[3],failed[3]);
    packet_fifo_case #(.WIDTH(13),.DEPTH(5),.CASE_ID(4)) wide_nonpower_case(clk,finished[4],failed[4]);
    packet_fifo_case #(.WIDTH(16),.DEPTH(8),.CASE_ID(5)) maximum_case(clk,finished[5],failed[5]);
    initial begin
        wait (&finished);
        #1;
        if (failed===6'b000000) $display("TEST PASSED");
        else $display("TEST FAILED: packet FIFO matrix failed mask=%b",failed);
        $finish;
    end
    initial begin
        #100000;
        $display("TEST FAILED: packet FIFO matrix watchdog");
        $finish;
    end
endmodule
