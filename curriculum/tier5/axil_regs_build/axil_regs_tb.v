`timescale 1ns/1ps
// Independent cycle-exact checker for the AXI4-Lite register slave. It models
// the held AW and W halves, the B and R responses and all eight registers,
// acts as an AXI master that keeps every offered VALID and payload stable until
// the model accepts it, checks every output port before and after each rising
// edge, and never reads DUT internals or the internal bank port.
module axil_regs_tb;
    reg clk=0, rst=1;
    reg awvalid=0, wvalid=0, bready=0, arvalid=0, rready=0;
    reg [5:0] awaddr=0, araddr=0;
    reg [31:0] wdata=0, status_in=0;
    reg [3:0] wstrb=0;
    reg [7:0] irq_set=0;
    wire awready, wready, bvalid, arready, rvalid, irq;
    wire [1:0] bresp, rresp;
    wire [31:0] rdata, ctrl;
    axil_regs dut(.clk(clk),.rst(rst),.awvalid(awvalid),.awready(awready),.awaddr(awaddr),
        .wvalid(wvalid),.wready(wready),.wdata(wdata),.wstrb(wstrb),.bvalid(bvalid),.bready(bready),
        .bresp(bresp),.arvalid(arvalid),.arready(arready),.araddr(araddr),.rvalid(rvalid),
        .rready(rready),.rdata(rdata),.rresp(rresp),.irq_set(irq_set),.status_in(status_in),
        .ctrl(ctrl),.irq(irq));
    always #5 clk=~clk;

    localparam [31:0] ID_VALUE = 32'h52544c35;
    // Reference state.
    reg m_awf=0, m_wf=0, m_bv=0, m_rv=0;
    reg [5:0] m_awa=0;
    reg [31:0] m_wd=0, m_rd=0;
    reg [3:0] m_ws=0;
    reg [1:0] m_br=0, m_rr=0;
    reg [31:0] m_reg [0:7];
    reg [31:0] lanes=0, clear=0;
    reg do_write=0, in_range=0, aw_hs=0, w_hs=0, b_hs=0, ar_hs=0, r_hs=0;
    // Master: a VALID offered and not accepted is held with its payload.
    reg aw_hold=0, w_hold=0, ar_hold=0, started=0;
    reg [5:0] aw_held=0, ar_held=0;
    reg [31:0] wd_held=0, irq_drive=0, status_drive=0, value=0;
    reg [3:0] ws_held=0;
    reg [7:0] irq_at_write=0;
    integer cycle=0, errors=0, i, j, t, s;
    integer writes_ok=0, writes_err=0, reads_ok=0, reads_err=0, w_first=0, aw_first=0, b_stalls=0;
    integer r_stalls=0, ar_waiting=0, held_pair_waiting=0, set_and_clear=0, irq_cycles=0, strobe_seen=0;
    integer busy_resets=0, pulses=0, ro_writes=0;
    reg [15:0] strobes_written=0;
    reg [31:0] seed=32'h2f6b9a1d;
    reg aw_done, w_done;

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
        input [31:0] v;
        reg [31:0] x;
        begin x=v^(v<<13); x=x^(x>>17); advance=x^(x<<5); end
    endfunction

    task model_reset;
        begin
            m_awf=0; m_wf=0; m_bv=0; m_rv=0; m_awa=0; m_wd=0; m_ws=0; m_br=0; m_rd=0; m_rr=0;
            m_reg[0]=0; m_reg[1]=0; m_reg[2]=32'h00000100; m_reg[3]=0;
            m_reg[4]=0; m_reg[5]=0; m_reg[6]=ID_VALUE; m_reg[7]=0;
        end
    endtask

    task check_ports;
        begin
            if(awready !== !m_awf) fail("awready_independent_of_w_channel");
            if(wready !== !m_wf) fail("wready_independent_of_aw_channel");
            if(bvalid !== m_bv) fail("bvalid_with_the_register_update");
            if(bresp !== m_br) fail("bresp_okay_or_slverr");
            if(arready !== !m_rv) fail("arready_one_read_outstanding");
            if(rvalid !== m_rv) fail("rvalid");
            if(rdata !== m_rd) fail("rdata_register_value_or_stall_hold");
            if(rresp !== m_rr) fail("rresp_okay_or_slverr");
            if(ctrl !== m_reg[0]) fail("ctrl_register_output");
            if(irq !== ((m_reg[3] & m_reg[4] & 32'hff) != 0)) fail("irq_masked_pending");
        end
    endtask

    // One clock cycle: inputs change at the falling edge, ports are checked
    // before the rising edge and after its updates. A held channel keeps
    // VALID and payload; reset abandons every held request.
    task step;
        input reset_now, awv;
        input [5:0] awa;
        input wv;
        input [31:0] wd;
        input [3:0] ws;
        input br, arv;
        input [5:0] ara;
        input rr;
        begin
            @(negedge clk);
            rst=reset_now; bready=br; rready=rr;
            if(aw_hold && !reset_now) begin awvalid=1; awaddr=aw_held; end
            else begin awvalid=awv; awaddr=awa; end
            if(w_hold && !reset_now) begin wvalid=1; wdata=wd_held; wstrb=ws_held; end
            else begin wvalid=wv; wdata=wd; wstrb=ws; end
            if(ar_hold && !reset_now) begin arvalid=1; araddr=ar_held; end
            else begin arvalid=arv; araddr=ara; end
            // irq_at_write lands on the edge where the model performs a write.
            irq_set=(m_awf && m_wf && !m_bv && irq_at_write!=0) ? irq_at_write : irq_drive[7:0];
            status_in=status_drive;
            #1; if(started) check_ports;
            @(posedge clk);
            cycle=cycle+1;
            do_write=m_awf && m_wf && !m_bv;
            in_range=!m_awa[5];
            aw_hs=!rst && awvalid && !m_awf;
            w_hs=!rst && wvalid && !m_wf;
            b_hs=!rst && m_bv && bready;
            ar_hs=!rst && arvalid && !m_rv;
            r_hs=!rst && m_rv && rready;
            aw_hold=!rst && awvalid && !aw_hs; aw_held=awaddr;
            w_hold=!rst && wvalid && !w_hs; wd_held=wdata; ws_held=wstrb;
            ar_hold=!rst && arvalid && !ar_hs; ar_held=araddr;
            if(rst) begin
                if(m_awf || m_wf || m_bv || m_rv) busy_resets=busy_resets+1;
                model_reset;
            end else begin
                if(m_bv && !bready) b_stalls=b_stalls+1;
                if(m_rv && !rready) r_stalls=r_stalls+1;
                if(m_rv && arvalid) ar_waiting=ar_waiting+1;
                if(m_awf && m_wf && m_bv) held_pair_waiting=held_pair_waiting+1;
                if(m_wf && !m_awf && !awvalid) w_first=w_first+1;
                if(m_awf && !m_wf && !wvalid) aw_first=aw_first+1;
                if((m_reg[3] & m_reg[4] & 32'hff)!=0) irq_cycles=irq_cycles+1;
                // Read channel samples the registers as they were before the edge.
                if(ar_hs) begin
                    m_rv=1;
                    if(araddr[5]) begin m_rd=0; m_rr=2'b10; reads_err=reads_err+1; end
                    else begin m_rd=m_reg[araddr[4:2]]; m_rr=2'b00; reads_ok=reads_ok+1; end
                end else if(r_hs) m_rv=0;
                // Register bank.
                clear=(do_write && in_range && m_awa[4:2]==3'd4 && m_ws[0]) ? (m_wd & 32'hff) : 32'd0;
                if((clear & irq_set)!=0) set_and_clear=set_and_clear+1;
                m_reg[4]=(m_reg[4] & ~clear) | irq_set;
                m_reg[5]=status_in;
                if(do_write && in_range) begin
                    m_reg[7]=m_reg[7]+1;
                    lanes={{8{m_ws[3]}},{8{m_ws[2]}},{8{m_ws[1]}},{8{m_ws[0]}}};
                    if(m_awa[4:2]<=3'd2) begin
                        m_reg[m_awa[4:2]]=(m_reg[m_awa[4:2]] & ~lanes) | (m_wd & lanes);
                        strobes_written[m_ws]=1'b1;
                    end
                    if(m_awa[4:2]==3'd3 && m_ws[0]) m_reg[3]=m_wd & 32'hff;
                    if(m_awa[4:2]>=3'd5) ro_writes=ro_writes+1;
                    writes_ok=writes_ok+1;
                end
                // Write channel.
                if(do_write) begin
                    m_awf=0; m_wf=0; m_bv=1; m_br=in_range ? 2'b00 : 2'b10;
                    if(!in_range) writes_err=writes_err+1;
                end else if(b_hs) m_bv=0;
                if(aw_hs) begin m_awf=1; m_awa=awaddr; end
                if(w_hs) begin m_wf=1; m_wd=wdata; m_ws=wstrb; end
            end
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

    task idle;
        input integer count;
        integer k;
        begin
            for(k=0;k<count;k=k+1) begin
                seed=advance(seed);
                step(0,0,seed[5:0],0,seed,seed[11:8],1,0,seed[17:12],1); // payload noise
            end
        end
    endtask

    // A complete write: AW offered from cycle aw_at and W from cycle w_at
    // (relative), then B accepted after b_wait stalled cycles.
    task axi_write;
        input [5:0] addr;
        input [31:0] data;
        input [3:0] strb;
        input integer aw_at, w_at, b_wait;
        begin
            aw_done=0; w_done=0; t=0;
            while(!aw_done || !w_done) begin
                step(0,!aw_done && t>=aw_at,addr,!w_done && t>=w_at,data,strb,0,0,6'd0,1);
                if(aw_hs) aw_done=1;
                if(w_hs) w_done=1;
                t=t+1;
            end
            while(!m_bv) step(0,0,6'd0,0,32'd0,4'd0,0,0,6'd0,1);
            s=0;
            while(m_bv) begin step(0,0,6'd0,0,32'd0,4'd0,s>=b_wait,0,6'd0,1); s=s+1; end
        end
    endtask

    // A complete read: AR offered at once, R accepted after r_wait stalled
    // cycles. The model's data is returned for the checker's own sanity checks.
    task axi_read;
        input [5:0] addr;
        input integer r_wait;
        begin
            step(0,0,6'd0,0,32'd0,4'd0,1,1,addr,0);
            while(!m_rv) step(0,0,6'd0,0,32'd0,4'd0,1,1,addr,0);
            value=m_rd;
            s=0;
            while(m_rv) begin step(0,0,6'd0,0,32'd0,4'd0,1,0,6'd0,s>=r_wait); s=s+1; end
        end
    endtask

    initial begin
        model_reset;
        status_drive=32'h0badf00d;
        step(1,0,6'd0,0,32'd0,4'd0,0,0,6'd0,0);
        step(1,1,6'h00,1,32'hffffffff,4'hf,1,1,6'h00,1); // reset dominates every channel
        // 1: reset values of all eight registers.
        for(i=0;i<8;i=i+1) begin
            axi_read(i*4,i%3);
            if(i==2 && value!==32'h100) checker_fail("config_reset_value");
            if(i==5 && value!==32'h0badf00d) checker_fail("status_snapshot");
            if(i==6 && value!==ID_VALUE) checker_fail("id_value");
        end
        // 2: every writable register with AW and W together, then read back.
        axi_write(6'h00,32'h11223344,4'hf,0,0,0); axi_write(6'h04,32'h55667788,4'hf,0,0,1);
        axi_write(6'h08,32'h99aabbcc,4'hf,0,0,0); axi_write(6'h0c,32'hffffff3c,4'hf,0,0,2);
        for(i=0;i<5;i=i+1) axi_read(i*4,1);
        // 3: W ahead of AW, AW ahead of W, and stalled responses.
        axi_write(6'h04,32'hdeadbeef,4'hf,3,0,0);
        axi_write(6'h08,32'hcafef00d,4'hf,0,4,5);
        axi_write(6'h00,32'h0f0f0f0f,4'hf,7,1,3);
        axi_read(6'h04,0); axi_read(6'h08,2); axi_read(6'h00,0);
        // 4: a second AW/W pair is captured while the first response is
        // stalled; it is written only after that response retires.
        step(0,1,6'h04,1,32'h01010101,4'hf,0,0,6'd0,1);
        step(0,0,6'd0,0,32'd0,4'd0,0,0,6'd0,1);
        if(!m_bv) checker_fail("pending_response_setup");
        for(i=0;i<6;i=i+1) step(0,1,6'h08,1,32'h02020202,4'hf,0,0,6'd0,1);
        if(!(m_awf && m_wf && m_bv)) checker_fail("held_pair_setup");
        for(i=0;i<4;i=i+1) step(0,0,6'd0,0,32'd0,4'd0,1,0,6'd0,1);
        axi_read(6'h04,0); axi_read(6'h08,0);
        // 5: all sixteen byte-strobe patterns on SCRATCH, each read back.
        for(i=0;i<16;i=i+1) begin
            seed=advance(seed);
            axi_write(6'h04,seed,i,i%2,(i/2)%2,i%3);
            axi_read(6'h04,i%2);
        end
        // 6: out-of-range writes (aliases of every index) and reads: SLVERR,
        // no register change, no write count.
        for(i=0;i<8;i=i+1) axi_write(6'h20+i*4+(i%4),32'hffffffff,4'hf,i%2,0,0);
        for(i=0;i<8;i=i+1) axi_read(i*4,0);
        axi_read(6'h20,1); axi_read(6'h33,0); axi_read(6'h3f,2);
        // 7: unaligned addresses select by bits 4:2 only.
        axi_write(6'h01,32'h13572468,4'hf,0,0,0); axi_write(6'h06,32'h24681357,4'h3,1,0,0);
        axi_read(6'h03,0); axi_read(6'h05,0); axi_read(6'h0b,0);
        // 8: interrupts: set pulses, mask, write-1-to-clear, clear with lane 0
        // disabled, upper-lane noise, and set and clear of one flag at one edge.
        irq_drive=8'h5a; step(0,0,6'd0,0,32'd0,4'd0,1,0,6'd0,1); irq_drive=0;
        axi_write(6'h0c,32'h000000f0,4'hf,0,0,0);
        axi_read(6'h10,0);
        axi_write(6'h10,32'h00000050,4'hf,0,0,1);
        axi_write(6'h10,32'h0000000a,4'he,0,0,0);
        axi_write(6'h10,32'hffffff00,4'hf,0,0,0);
        axi_read(6'h10,0);
        irq_at_write=8'h22; axi_write(6'h10,32'h000000ff,4'h1,0,0,0); irq_at_write=0;
        axi_read(6'h10,0);
        axi_write(6'h0c,32'h00000000,4'he,0,0,0);
        axi_write(6'h0c,32'h00000000,4'h1,0,0,0);
        irq_drive=8'h81; step(0,0,6'd0,0,32'd0,4'd0,1,0,6'd0,1); irq_drive=0;
        axi_write(6'h0c,32'h00000080,4'h1,0,0,0);
        axi_write(6'h10,32'h00000081,4'h1,0,0,0);
        // 9: read-only registers ignore writes but count them.
        axi_write(6'h14,32'h11111111,4'hf,0,0,0); axi_write(6'h18,32'h22222222,4'hf,0,0,0);
        axi_write(6'h1c,32'h33333333,4'hf,0,0,0);
        status_drive=32'h600df00d; idle(1);
        axi_read(6'h14,0); axi_read(6'h18,0); axi_read(6'h1c,0);
        // 10: read at the very edge a write lands returns the old value; the
        // next read returns the new value.
        step(0,1,6'h00,1,32'habcdef01,4'hf,0,0,6'd0,1);
        step(0,0,6'd0,0,32'd0,4'd0,0,1,6'h00,1);
        step(0,0,6'd0,0,32'd0,4'd0,1,0,6'd0,1);
        axi_read(6'h00,0);
        idle(2);
        // 11: R stalled while the next AR is held high: the second read is
        // accepted only after the first R transfer.
        step(0,0,6'd0,0,32'd0,4'd0,1,1,6'h08,0);
        for(i=0;i<5;i=i+1) step(0,0,6'd0,0,32'd0,4'd0,1,1,6'h18,0);
        step(0,0,6'd0,0,32'd0,4'd0,1,0,6'd0,1);
        for(i=0;i<3;i=i+1) step(0,0,6'd0,0,32'd0,4'd0,1,1,6'h04,(i==2));
        idle(3);
        // 12: synchronous reset with a held pair behind a stalled response, a
        // stalled read and nonzero registers; then everything restarts.
        step(0,1,6'h04,1,32'h77777777,4'hf,0,1,6'h00,0);
        step(0,1,6'h08,1,32'h88888888,4'hf,0,0,6'd0,0);
        step(0,0,6'd0,0,32'd0,4'd0,0,0,6'd0,0);
        if(!(m_bv && m_awf && m_wf && m_rv)) checker_fail("reset_setup");
        step(1,1,6'h0c,1,32'hffffffff,4'hf,0,1,6'h1c,0);
        for(i=0;i<8;i=i+1) axi_read(i*4,0);
        // 13: off-edge reset pulses with every channel busy and nonzero state.
        axi_write(6'h00,32'h5a5a5a5a,4'hf,0,0,0);
        irq_drive=8'h0f; step(0,0,6'd0,0,32'd0,4'd0,1,0,6'd0,1); irq_drive=0;
        axi_write(6'h0c,32'h0000000f,4'h1,0,0,0);
        step(0,1,6'h04,1,32'h66666666,4'hf,0,1,6'h00,0);
        step(0,1,6'h08,1,32'h99999999,4'hf,0,0,6'd0,0);
        pulse_reset;
        step(0,0,6'd0,0,32'd0,4'd0,0,0,6'd0,0);
        pulse_reset;
        for(i=0;i<6;i=i+1) step(0,0,6'd0,0,32'd0,4'd0,1,0,6'd0,1);
        // 14: seeded random master traffic with three synchronous resets.
        for(i=0;i<3000;i=i+1) begin
            seed=advance(seed);
            status_drive=advance(seed^32'h85ebca6b);
            irq_drive=(seed[30:28]==3'b000) ? {24'd0,seed[27:20]} : 32'd0;
            value=advance(status_drive);
            step(i==900 || i==1800 || i==2600,
                 seed[0], {seed[1] & seed[2], seed[5:3], value[1:0]},
                 seed[6], value, seed[10:7],
                 (i%50)<30 ? seed[11] | seed[12] : seed[11] & seed[12],
                 seed[13], {seed[14] & seed[15], seed[18:16], value[3:2]},
                 (i%40)<25 ? seed[19] | seed[20] : seed[19] & seed[20]);
        end
        // Drain every channel.
        for(i=0;i<8;i=i+1) step(0,0,6'd0,0,32'd0,4'd0,1,0,6'd0,1);
        if(m_awf || m_wf || m_bv || m_rv || aw_hold || w_hold || ar_hold) checker_fail("final_drain");
        if(writes_ok<500 || writes_err<100 || reads_ok<500 || reads_err<100) coverage_fail("transactions");
        if(w_first<30 || aw_first<30 || b_stalls<100 || r_stalls<100 || ar_waiting<100 || held_pair_waiting<50)
            coverage_fail("channel_independence_and_stalls");
        if(strobes_written!=16'hffff || set_and_clear<1 || irq_cycles<50 || ro_writes<3)
            coverage_fail("register_semantics");
        if(busy_resets<4 || pulses!=2) coverage_fail("resets");
        $display("COVERAGE cycles=%0d writes_ok=%0d writes_err=%0d reads_ok=%0d reads_err=%0d w_first=%0d aw_first=%0d b_stalls=%0d r_stalls=%0d ar_waiting=%0d held_pair=%0d set_and_clear=%0d irq_cycles=%0d ro_writes=%0d busy_resets=%0d pulses=%0d",
            cycle,writes_ok,writes_err,reads_ok,reads_err,w_first,aw_first,b_stalls,r_stalls,ar_waiting,
            held_pair_waiting,set_and_clear,irq_cycles,ro_writes,busy_resets,pulses);
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
