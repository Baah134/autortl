`timescale 1ns/1ps
module skid_buffer_tb;
    reg clk=0, rst=1, in_valid=0, out_ready=0;
    reg [7:0] in_data=0;
    wire in_ready, out_valid;
    wire [7:0] out_data;
    skid_buffer dut(.clk(clk),.rst(rst),.in_data(in_data),.in_valid(in_valid),
        .in_ready(in_ready),.out_data(out_data),.out_valid(out_valid),.out_ready(out_ready));
    always #5 clk=~clk;

    // Independent SHIFT queue: no reference to DUT storage, pointers or count.
    reg [7:0] expected0, expected1;
    integer queued=0, errors=0, checked=0;
    integer accepted=0, retired=0, discarded=0, full_cycles=0;
    integer stalled_cycles=0, simultaneous=0, bubble_cycles=0, empty_cycles=0;
    integer reset_occupied=0, max_queued=0;
    reg model_started=0, push, pop, last_push=0;
    reg pending_valid=0;
    reg [7:0] pending_data=0;
    reg [31:0] seed=32'h793ac4e1;
    integer i;

    task fail;
        input [511:0] message;
        begin
            errors=errors+1;
            if(errors<=12) $display("FAIL cycle=%0d queued=%0d: %0s",checked,queued,message);
        end
    endtask
    task check_outputs;
        begin
            if(out_valid !== (queued!=0)) fail("out_valid must equal nonempty queue");
            if(in_ready !== ((queued<2)||out_ready)) fail("in_ready capacity/full-pop rule");
            if(queued>0 && out_data !== expected0) fail("oldest payload/order/stall stability");
        end
    endtask
    task step;
        input reset_value, valid_value;
        input [7:0] data_value;
        input ready_value;
        begin
            @(negedge clk);
            rst=reset_value; in_valid=valid_value; in_data=data_value; out_ready=ready_value;
            #1;
            // Catches empty fallthrough and asynchronous reset while occupied.
            if(model_started) check_outputs;
            @(posedge clk);
            if(model_started) check_outputs; // BEFORE DUT nonblocking updates
            push=in_valid && ((queued<2)||out_ready);
            pop=(queued>0) && out_ready;
            last_push=0;
            if(rst) begin
                if(queued>0) reset_occupied=reset_occupied+1;
                discarded=discarded+queued;
                queued=0;
            end else begin
                if(queued==2) full_cycles=full_cycles+1;
                if(queued==0) empty_cycles=empty_cycles+1;
                if(queued>0 && !out_ready) stalled_cycles=stalled_cycles+1;
                if(!in_valid) bubble_cycles=bubble_cycles+1;
                if(push && pop) simultaneous=simultaneous+1;
                // Retire FIRST, then append; model uses no DUT handshake output.
                if(pop) begin
                    expected0=expected1;
                    queued=queued-1;
                    retired=retired+1;
                end
                if(push) begin
                    if(queued==0) expected0=in_data;
                    else expected1=in_data;
                    queued=queued+1;
                    accepted=accepted+1;
                    last_push=1;
                end
            end
            if(queued>max_queued) max_queued=queued;
            if(queued<0 || queued>2) fail("reference queue bounds");
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
            x=value^(value<<13); x=x^(x>>17); x=x^(x<<5); advance=x;
        end
    endfunction
    initial begin
        step(1,0,0,0); step(1,0,0,0);
        step(0,1,8'h10,0); step(0,1,8'h20,0);
        // Third word must remain pending until space is available.
        repeat(6) step(0,1,8'h30,0);
        step(0,1,8'h30,1); step(0,1,8'h40,1);
        step(0,0,0,0); step(0,0,0,1); step(0,0,0,1);
        repeat(4) step(0,0,0,1);
        // Long throughput run covers every 8-bit payload and repeated wraps.
        for(i=0;i<256;i=i+1) step(0,1,i[7:0],1);
        repeat(4) step(0,0,0,1);
        // Reset must discard two queued words at the edge, not before it.
        step(0,1,8'h91,0); step(0,1,8'h92,0);
        step(1,1,8'h93,0); step(0,1,8'h93,0);
        repeat(4) step(0,0,0,1);
        for(i=0;i<600;i=i+1) begin
            seed=advance(seed);
            if(!pending_valid || last_push) begin
                pending_valid=seed[0]||seed[3];
                pending_data=seed[15:8];
            end
            step((i==173)||(i==421),pending_valid,pending_data,seed[2]||seed[7]);
        end
        // Finish any producer-held word before withdrawing valid.
        if(pending_valid && !last_push) step(0,1,pending_data,1);
        repeat(6) step(0,0,0,1);
        if(queued!=0 || accepted!=retired+discarded) fail("final drain/accounting");
        if(checked<850 || accepted<300 || retired<300 || max_queued!=2 ||
           full_cycles<4 || stalled_cycles<4 || simultaneous<200 ||
           bubble_cycles<2 || empty_cycles<4 || reset_occupied<1)
            fail("required scenario coverage missing");
        $display("COVERAGE checked=%0d accepted=%0d retired=%0d discarded=%0d full=%0d stall=%0d simultaneous=%0d resets_occupied=%0d",checked,accepted,retired,discarded,full_cycles,stalled_cycles,simultaneous,reset_occupied);
        if(errors==0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors",errors);
        $finish;
    end
    initial begin
        #100000;
        $display("TEST FAILED: watchdog");
        $finish;
    end
endmodule
