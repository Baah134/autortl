`timescale 1ns/1ps
// Every case owns its own shift queue and temporal assertions; no DUT internals.
module sync_fifo_case #(parameter WIDTH=8, DEPTH=3, USE_TOP=0, CASE_ID=0)(
    input clk, output reg finished=0, output reg failed=0);
    reg rst=1, in_valid=0, out_ready=0;
    reg [WIDTH-1:0] in_data=0;
    wire in_ready, out_valid;
    wire [WIDTH-1:0] out_data;
    generate
        if(USE_TOP) begin: default_wrapper
            sync_fifo_core dut(.clk(clk),.rst(rst),.in_data(in_data),.in_valid(in_valid),
                .in_ready(in_ready),.out_data(out_data),.out_valid(out_valid),.out_ready(out_ready));
        end else begin: parameter_child
            sync_fifo_core #(.WIDTH(WIDTH),.DEPTH(DEPTH)) dut(.clk(clk),.rst(rst),
                .in_data(in_data),.in_valid(in_valid),.in_ready(in_ready),
                .out_data(out_data),.out_valid(out_valid),.out_ready(out_ready));
        end
    endgenerate
    reg [WIDTH-1:0] expected_queue [0:DEPTH-1];
    integer queued=0, errors=0, checked=0, accepted=0, retired=0, discarded=0;
    integer full_cycles=0, stalled=0, simultaneous=0, empty_cycles=0, bubbles=0;
    integer resets_occupied=0, max_queued=0, i, shift_index;
    reg model_started=0, push, pop, last_push=0, pending_valid=0;
    reg [WIDTH-1:0] pending_data=0;
    reg [31:0] seed=32'h9e3779b9 ^ CASE_ID;
    task fail;
        input [511:0] message;
        begin
            errors=errors+1;
            if(errors<=10) $display("FAIL case=%0d WIDTH=%0d DEPTH=%0d cycle=%0d queued=%0d: %0s",CASE_ID,WIDTH,DEPTH,checked,queued,message);
        end
    endtask
    task check_outputs;
        begin
            if(out_valid !== (queued!=0)) fail("nonempty validity/no empty bypass");
            if(in_ready !== ((queued<DEPTH)||out_ready)) fail("capacity/full simultaneous readiness");
            if(queued>0 && out_data !== expected_queue[0]) fail("oldest full-width payload/order/stall stability");
        end
    endtask
    task step;
        input reset_value, valid_value;
        input [WIDTH-1:0] data_value;
        input ready_value;
        begin
            @(negedge clk);
            rst=reset_value; in_valid=valid_value; in_data=data_value; out_ready=ready_value;
            #1;
            if(model_started) check_outputs; // before capture; catches async reset/empty bypass
            @(posedge clk);
            if(model_started) check_outputs; // before DUT NBA
            push=in_valid && ((queued<DEPTH)||out_ready);
            pop=(queued>0) && out_ready;
            last_push=0;
            if(rst) begin
                resets_occupied=resets_occupied+(queued>0);
                discarded=discarded+queued;
                queued=0;
            end else begin
                full_cycles=full_cycles+(queued==DEPTH);
                stalled=stalled+((queued>0)&&!out_ready);
                simultaneous=simultaneous+(push&&pop);
                empty_cycles=empty_cycles+(queued==0);
                bubbles=bubbles+!in_valid;
                // Independent queue shifts on retirement, then appends on capture.
                if(pop) begin
                    for(shift_index=0;shift_index<DEPTH-1;shift_index=shift_index+1)
                        expected_queue[shift_index]=expected_queue[shift_index+1];
                    queued=queued-1;
                    retired=retired+1;
                end
                if(push) begin
                    expected_queue[queued]=in_data;
                    queued=queued+1;
                    accepted=accepted+1;
                    last_push=1;
                end
            end
            if(queued>max_queued) max_queued=queued;
            if(queued<0 || queued>DEPTH) fail("reference bounds");
            #1; model_started=1; check_outputs; checked=checked+1;
            #1;
        end
    endtask
    function [31:0] advance;
        input [31:0] value;
        reg [31:0] x;
        begin x=value^(value<<13); x=x^(x>>17); x=x^(x<<5); advance=x; end
    endfunction
    function [WIDTH-1:0] payload;
        input integer index;
        reg [31:0] value;
        begin value=(index*137)+(CASE_ID*53)+32'h1a35; payload=value; end
    endfunction
    initial begin
        step(1,0,0,0); step(1,0,0,0);
        // Fill exactly DEPTH slots. The next input must remain unaccepted.
        for(i=0;i<DEPTH;i=i+1) step(0,1,payload(i),0);
        repeat(6) step(0,1,{WIDTH{1'b1}},0);
        step(0,1,{WIDTH{1'b1}},1);
        for(i=0;i<4*DEPTH+8;i=i+1) step(0,1,payload(i+32),1);
        repeat(DEPTH+3) step(0,0,0,1);
        // High bits and every 8-bit pattern are visible in wider configurations.
        step(0,1,(1 << (WIDTH-1))|1,1);
        step(0,1,{WIDTH{1'b1}},1);
        for(i=0;i<256;i=i+1) step(0,1,payload(i),1);
        repeat(DEPTH+3) step(0,0,0,1);
        for(i=0;i<DEPTH;i=i+1) step(0,1,payload(i+100),0);
        step(1,1,{WIDTH{1'b1}},0); // all queued words discarded only at rising edge
        step(0,1,{WIDTH{1'b1}},0);
        repeat(DEPTH+3) step(0,0,0,1);
        for(i=0;i<400;i=i+1) begin
            seed=advance(seed);
            if(!pending_valid || last_push) begin
                pending_valid=seed[0]||seed[3];
                pending_data=seed[WIDTH-1:0];
            end
            step((i==131)||(i==317),pending_valid,pending_data,seed[2]||seed[7]);
        end
        if(pending_valid && !last_push) step(0,1,pending_data,1);
        repeat(DEPTH+5) step(0,0,0,1);
        if(queued!=0 || accepted!=retired+discarded) fail("final drain/transaction accounting");
        if(checked<650 || accepted<300 || retired<290 || max_queued!=DEPTH ||
           full_cycles<6 || stalled<6 || simultaneous<200 || empty_cycles<4 ||
           bubbles<2 || resets_occupied<1) fail("required scenario coverage missing");
        $display("COVERAGE case=%0d WIDTH=%0d DEPTH=%0d checked=%0d accepted=%0d retired=%0d discarded=%0d full=%0d stall=%0d simultaneous=%0d resets=%0d",CASE_ID,WIDTH,DEPTH,checked,accepted,retired,discarded,full_cycles,stalled,simultaneous,resets_occupied);
        failed=(errors!=0); finished=1;
    end
endmodule

module sync_fifo_core_tb;
    reg clk=0;
    wire [5:0] finished, failed;
    always #5 clk=~clk;
    sync_fifo_case #(.WIDTH(8),.DEPTH(3),.USE_TOP(1),.CASE_ID(0)) default_case(clk,finished[0],failed[0]);
    sync_fifo_case #(.WIDTH(1),.DEPTH(1),.CASE_ID(1)) depth1_case(clk,finished[1],failed[1]);
    sync_fifo_case #(.WIDTH(8),.DEPTH(2),.CASE_ID(2)) depth2_case(clk,finished[2],failed[2]);
    sync_fifo_case #(.WIDTH(8),.DEPTH(4),.CASE_ID(3)) depth4_case(clk,finished[3],failed[3]);
    sync_fifo_case #(.WIDTH(13),.DEPTH(5),.CASE_ID(4)) wide_nonpower_case(clk,finished[4],failed[4]);
    sync_fifo_case #(.WIDTH(16),.DEPTH(8),.CASE_ID(5)) maximum_case(clk,finished[5],failed[5]);
    initial begin
        wait(&finished); #1;
        if(failed===6'b000000) $display("TEST PASSED");
        else $display("TEST FAILED: FIFO matrix failed mask=%b",failed);
        $finish;
    end
    initial begin
        #100000;
        $display("TEST FAILED: FIFO matrix watchdog");
        $finish;
    end
endmodule
