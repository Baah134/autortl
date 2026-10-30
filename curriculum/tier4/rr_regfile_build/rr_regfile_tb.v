`timescale 1ns/1ps
// Independent integration checker for the arbiter + register file hierarchy.
// It models round-robin arbitration, the registered write port and the
// read-first register file itself, observes only the top ports (grant and
// rd_data), and never reads DUT internals or the internal write channel.
module rr_regfile_tb;
    reg clk=0, rst=1;
    reg [3:0] req=0;
    reg [2:0] addr0=0, addr1=0, addr2=0, addr3=0, rd_addr=0;
    reg [7:0] data0=0, data1=0, data2=0, data3=0;
    wire [3:0] grant;
    wire [7:0] rd_data;
    rr_regfile dut(.clk(clk),.rst(rst),.req(req),.addr0(addr0),.data0(data0),
        .addr1(addr1),.data1(data1),.addr2(addr2),.data2(data2),.addr3(addr3),
        .data3(data3),.rd_addr(rd_addr),.grant(grant),.rd_data(rd_data));
    always #5 clk=~clk;

    // Reference state: arbiter pointer and registered write port, memory,
    // registered read data.
    integer m_last=3, m_winner=0;
    reg [3:0] m_grant=0;
    reg m_wen=0, started=0, nonzero=0;
    reg [2:0] m_waddr=0;
    reg [7:0] m_wdata=0, m_rd=0, next_rd=0;
    reg [7:0] m_mem [0:7];
    integer grants [0:3];
    reg [15:0] patterns=0;
    integer cycle=0, errors=0, collisions=0, idle_cycles=0, pending_resets=0;
    integer nonzero_resets=0, pulses=0, i, k, idx;
    reg [31:0] seed=32'h7f4a7c15;
    reg [3:0] random_req;

    task fail;
        input [511:0] rule;
        begin
            errors=errors+1;
            if(errors<=40) $display("FAIL BEHAVIOR rule=%0s cycle=%0d",rule,cycle);
        end
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

    task check_outputs;
        begin
            if(grant !== m_grant) fail("round_robin_one_hot_grant");
            if(rd_data !== m_rd) fail("read_first_register_file_data");
        end
    endtask

    // One clock cycle. Inputs change at the falling edge; outputs must hold
    // between edges and match the model after each rising edge.
    task step;
        input reset_value;
        input [3:0] req_value;
        input [11:0] addr_value;  // {addr3,addr2,addr1,addr0}
        input [31:0] data_value;  // {data3,data2,data1,data0}
        input [2:0] read_value;
        begin
            @(negedge clk);
            rst=reset_value; req=req_value; rd_addr=read_value;
            {addr3,addr2,addr1,addr0}=addr_value;
            {data3,data2,data1,data0}=data_value;
            #1; if(started) check_outputs;
            @(posedge clk);
            cycle=cycle+1;
            if(rst) begin
                if(m_wen) pending_resets=pending_resets+1;
                nonzero=0;
                for(k=0;k<8;k=k+1) if(m_mem[k]!=0) nonzero=1;
                if(nonzero) nonzero_resets=nonzero_resets+1;
                for(k=0;k<8;k=k+1) m_mem[k]=0;
                m_last=3; m_grant=0; m_wen=0; m_waddr=0; m_wdata=0; m_rd=0;
            end else begin
                // Register file: read the old contents, then apply the write
                // registered by the arbiter at the previous edge.
                next_rd=m_mem[read_value];
                if(m_wen && m_waddr==read_value) collisions=collisions+1;
                if(m_wen) m_mem[m_waddr]=m_wdata;
                m_rd=next_rd;
                // Arbiter: first requester after the last winner, cyclically.
                patterns[req_value]=1'b1;
                m_winner=-1;
                for(k=1;k<=4;k=k+1) begin
                    idx=(m_last+k)%4;
                    if(m_winner<0 && req_value[idx]) m_winner=idx;
                end
                if(m_winner>=0) begin
                    m_grant=4'b0001<<m_winner;
                    m_wen=1;
                    m_waddr=addr_value>>(3*m_winner);
                    m_wdata=data_value>>(8*m_winner);
                    m_last=m_winner;
                    grants[m_winner]=grants[m_winner]+1;
                end else begin
                    m_grant=0; m_wen=0; m_waddr=0; m_wdata=0;
                    idle_cycles=idle_cycles+1;
                end
            end
            #1; started=1; check_outputs;
        end
    endtask

    task rand_step;
        input reset_value;
        input [3:0] req_value;
        input [2:0] read_value;
        reg [11:0] addresses;
        begin
            seed=advance(seed); addresses=seed[11:0];
            seed=advance(seed);
            step(reset_value,req_value,addresses,seed,read_value);
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

    initial begin
        for(k=0;k<8;k=k+1) m_mem[k]=0;
        for(k=0;k<4;k=k+1) grants[k]=0;
        step(1,4'b0000,12'h000,32'h00000000,3'd0);
        step(1,4'b1111,12'hfff,32'hffffffff,3'd7); // reset blocks arbitration and writes
        // 1: all four request; grants rotate 0,1,2,3 with distinct addresses.
        for(i=0;i<16;i=i+1) begin
            seed=advance(seed);
            step(0,4'b1111,{i[2:0]+3'd3,i[2:0]+3'd2,i[2:0]+3'd1,i[2:0]},seed,i[2:0]+3'd5);
        end
        // 2: every request pattern for three consecutive cycles.
        for(i=0;i<16;i=i+1) begin
            rand_step(0,i,i[2:0]); rand_step(0,i,i[2:0]+3'd1); rand_step(0,i,i[2:0]+3'd2);
        end
        // 3: a lone requester is granted at every edge.
        for(i=0;i<4;i=i+1) begin
            rand_step(0,4'b0001<<i,3'd0); rand_step(0,4'b0001<<i,3'd1);
            rand_step(0,4'b0001<<i,3'd2); rand_step(0,4'b0001<<i,3'd3);
        end
        // 4: read-first collisions: requester 2 rewrites entry 5 every cycle
        // while entry 5 is read.
        for(i=0;i<8;i=i+1) begin
            seed=advance(seed);
            step(0,4'b0100,{3'd0,3'd5,3'd0,3'd0},seed,3'd5);
        end
        // 5: entry 0 keeps 0xC3 through idle cycles with noisy write inputs.
        step(0,4'b0001,12'h000,32'h000000c3,3'd0);
        for(i=0;i<6;i=i+1) begin
            seed=advance(seed);
            step(0,4'b0000,seed[11:0],seed,3'd0);
        end
        // 6: fill every entry, reset with a write pending, then check that the
        // pointer restarts at requester 0 and every entry reads zero.
        for(i=0;i<8;i=i+1) step(0,4'b0001,{9'd0,i[2:0]},{24'd0,8'h41+i[7:0]},i[2:0]);
        step(0,4'b0001,12'h007,32'h00000099,3'd7);
        step(1,4'b1111,12'hfff,32'hffffffff,3'd2);
        for(i=0;i<7;i=i+1) step(0,4'b1111,12'hfff,32'h5a5a5a5a,i[2:0]);
        step(0,4'b0000,12'h000,32'h00000000,3'd7);
        // 7: off-edge reset pulses with nonzero grant, read data and entries.
        for(i=0;i<8;i=i+1) step(0,4'b0010,{6'd0,i[2:0],3'd0},{16'd0,8'h81+i[7:0],8'd0},3'd6);
        step(0,4'b1010,12'h000,32'h00000000,3'd3);
        pulse_reset;
        step(0,4'b1010,12'h000,32'h00000000,3'd4);
        pulse_reset;
        for(i=0;i<8;i=i+1) step(0,4'b0000,12'h000,32'h00000000,i[2:0]);
        // 8: seeded random traffic with two synchronous resets.
        for(i=0;i<1500;i=i+1) begin
            seed=advance(seed);
            random_req=seed[3:0];
            rand_step(i==500 || i==1100,random_req,seed[6:4]);
        end
        // 9: read every entry back while idle.
        for(i=0;i<10;i=i+1) rand_step(0,4'b0000,i[2:0]);
        if(patterns!=16'hffff) coverage_fail("request_patterns");
        if(grants[0]<100 || grants[1]<100 || grants[2]<100 || grants[3]<100) coverage_fail("grants_per_requester");
        if(collisions<50 || idle_cycles<40) coverage_fail("collisions_idle");
        if(pending_resets<1 || nonzero_resets<1 || pulses!=2) coverage_fail("reset_pulses");
        $display("COVERAGE cycles=%0d grants=%0d/%0d/%0d/%0d collisions=%0d idle=%0d pending_resets=%0d nonzero_resets=%0d pulses=%0d",
            cycle,grants[0],grants[1],grants[2],grants[3],collisions,idle_cycles,pending_resets,nonzero_resets,pulses);
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
