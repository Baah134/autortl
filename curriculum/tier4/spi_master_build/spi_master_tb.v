`timescale 1ns/1ps
// Independent cycle-exact SPI mode-0 checker. Each case owns a reference model
// of the bus schedule and an SPI slave that drives MISO with the correct bit
// only in the cycle before each specified sample edge (noise otherwise). No DUT
// internals are read; stimulus follows the model, so a stuck DUT still ends.
module spi_master_case #(parameter HALF=2, parameter USE_TOP=0, parameter CASE_ID=0)(
    input clk, output reg finished=0, output reg failed=0, output reg [31:0] error_count=0);
    reg rst=1, cmd_valid=0, rsp_ready=0, miso=0;
    reg [7:0] cmd_data=0;
    wire cmd_ready, rsp_valid, sclk, mosi, cs_n;
    wire [7:0] rsp_data;
    generate
        if (USE_TOP) begin: default_wrapper
            spi_master dut(.clk(clk),.rst(rst),.cmd_data(cmd_data),.cmd_valid(cmd_valid),
                .cmd_ready(cmd_ready),.rsp_data(rsp_data),.rsp_valid(rsp_valid),
                .rsp_ready(rsp_ready),.sclk(sclk),.mosi(mosi),.miso(miso),.cs_n(cs_n));
        end else begin: parameter_child
            spi_master_core #(.HALF_PERIOD(HALF)) dut(.clk(clk),.rst(rst),.cmd_data(cmd_data),
                .cmd_valid(cmd_valid),.cmd_ready(cmd_ready),.rsp_data(rsp_data),
                .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.sclk(sclk),.mosi(mosi),
                .miso(miso),.cs_n(cs_n));
        end
    endgenerate

    localparam FRAME = 16*HALF;
    // Reference model: m_t counts rising edges since the accepting edge.
    reg m_busy=0, m_rsp_valid=0;
    integer m_t=0;
    reg [7:0] m_tx=0, m_slave=0, m_rx=0, m_rsp=0, next_slave=0;
    reg started=0, blocked=0, accept=0, pop=0, last_accept=0, exp_sclk=0, exp_mosi=0;
    reg [7:0] held_data=0;
    integer checked=0, errors=0, accepted=0, retired=0, aborted_busy=0, aborted_rsp=0;
    integer stalled_rsp=0, blocked_cmd=0, pulses=0, directed=0, random_transfers=0;
    integer phase, n, guard, half_index;
    reg [31:0] seed=32'h2545f491 ^ CASE_ID;

    task fail;
        input [511:0] rule;
        begin
            errors=errors+1;
            if(errors<=12) $display("FAIL BEHAVIOR case=%0d HALF=%0d step=%0d t=%0d rule=%0s",CASE_ID,HALF,checked,m_t,rule);
        end
    endtask
    task checker_fail;
        input [511:0] rule;
        begin errors=errors+1; $display("CHECKER_FAIL case=%0d HALF=%0d step=%0d rule=%0s",CASE_ID,HALF,checked,rule); end
    endtask
    task coverage_fail;
        input [511:0] rule;
        begin errors=errors+1; $display("COVERAGE_FAIL case=%0d HALF=%0d rule=%0s",CASE_ID,HALF,rule); end
    endtask

    function [31:0] advance;
        input [31:0] value;
        reg [31:0] x;
        begin x=value^(value<<13); x=x^(x>>17); advance=x^(x<<5); end
    endfunction

    task check_outputs;
        begin
            if(m_busy) begin
                half_index=m_t/HALF;          // SCLK toggles completed, 0..15
                exp_sclk=half_index%2;
                exp_mosi=m_tx[7-half_index/2];
            end else begin
                exp_sclk=0; exp_mosi=0;
            end
            if(cmd_ready !== (!m_busy && !m_rsp_valid)) fail("cmd_ready_single_outstanding");
            if(rsp_valid !== m_rsp_valid) fail("rsp_valid_exact_availability");
            if(m_rsp_valid && rsp_data !== m_rsp) fail("rsp_data_miso_sample_or_stall_hold");
            if(cs_n !== !m_busy) fail("cs_n_framing");
            if(sclk !== exp_sclk) fail("sclk_mode0_half_period");
            if(mosi !== exp_mosi) fail("mosi_msb_first_falling_edge");
        end
    endtask

    // One clock cycle: inputs change at the falling edge and ports are checked
    // before the rising edge and after its updates. A blocked command is held
    // unchanged until accepted, except that reset aborts it.
    task step;
        input reset_value, valid_value;
        input [7:0] data_value;
        input ready_value;
        begin
            @(negedge clk);
            rst=reset_value; rsp_ready=ready_value;
            if(blocked && !reset_value) begin cmd_valid=1; cmd_data=held_data; end
            else begin cmd_valid=valid_value; cmd_data=data_value; end
            seed=advance(seed);
            // Slave: the correct bit only right before a specified sample edge.
            if(m_busy && ((m_t+1)%(2*HALF))==HALF) miso=m_slave[7-(m_t+1-HALF)/(2*HALF)];
            else miso=seed[9];
            #1; if(started) check_outputs;
            @(posedge clk);
            accept=!rst && cmd_valid && !m_busy && !m_rsp_valid;
            pop=!rst && m_rsp_valid && rsp_ready;
            blocked=!rst && cmd_valid && !accept;
            held_data=cmd_data;
            last_accept=accept;
            if(rst) begin
                if(m_busy) aborted_busy=aborted_busy+1;
                if(m_rsp_valid) aborted_rsp=aborted_rsp+1;
                m_busy=0; m_rsp_valid=0; m_t=0;
            end else begin
                if(m_rsp_valid && !rsp_ready) stalled_rsp=stalled_rsp+1;
                if(blocked) blocked_cmd=blocked_cmd+1;
                if(pop) begin m_rsp_valid=0; retired=retired+1; end
                if(m_busy) begin
                    m_t=m_t+1;
                    if((m_t%(2*HALF))==HALF) m_rx={m_rx[6:0],miso};
                    if(m_t==FRAME) begin
                        m_busy=0; m_rsp_valid=1; m_rsp=m_rx;
                        if(m_rx !== m_slave) checker_fail("slave_byte_model");
                    end
                end else if(accept) begin
                    m_busy=1; m_t=0; m_tx=cmd_data; m_slave=next_slave;
                    accepted=accepted+1;
                end
            end
            #1; started=1; check_outputs; checked=checked+1;
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

    task finish_transfer;
        input integer stall;
        integer s;
        begin
            while(m_busy) begin seed=advance(seed); step(0,0,seed[7:0],1); end // noise on cmd_data
            for(s=0;s<stall;s=s+1) begin seed=advance(seed); step(0,0,seed[15:8],0); end
            step(0,0,8'h00,1); // retire
        end
    endtask

    task transaction;
        input [7:0] tx, slave;
        input integer stall;
        begin
            next_slave=slave;
            step(0,1,tx,1);
            if(!last_accept) checker_fail("directed_not_idle");
            finish_transfer(stall);
            directed=directed+1;
        end
    endtask

    initial begin
        step(1,0,8'h00,0);
        step(1,1,8'h81,1); // reset dominates an offered command
        // Directed transfers: patterns, extremes and asymmetric slave bytes.
        transaction(8'ha5,8'h3c,0);
        transaction(8'h5a,8'hc3,3);
        transaction(8'h00,8'hff,1);
        transaction(8'hff,8'h00,2);
        transaction(8'h80,8'h01,0);
        transaction(8'h01,8'h80,4);
        // A second command waits through the transfer, the stalled response
        // and the retirement edge; it is accepted only at the following edge.
        next_slave=8'h96;
        step(0,1,8'hc6,1);
        if(!last_accept) checker_fail("first_burst_setup");
        step(0,1,8'h3b,0);
        while(m_busy) step(0,1,8'h00,0);
        repeat(3) step(0,1,8'h00,0);
        next_slave=8'h69;
        step(0,1,8'h00,1);
        if(last_accept) checker_fail("model_accept_on_retire");
        step(0,1,8'h00,1);
        if(!last_accept || m_tx !== 8'h3b) checker_fail("held_command_setup");
        finish_transfer(1);
        // Reset at every transfer phase, at the response edge and while a
        // stalled response is held; a second command is blocked meanwhile.
        for(phase=0;phase<=FRAME+2;phase=phase+1) begin
            next_slave=phase*29+7;
            step(0,1,phase*53+17,0);
            if(!last_accept) checker_fail("reset_phase_setup");
            for(n=0;n<phase;n=n+1) step(0,1,8'h5a,0);
            step(1,1,8'ha5,1);
            step(0,0,8'h00,1);
        end
        // Off-edge reset pulses during a transfer and during a held response.
        next_slave=8'he7;
        step(0,1,8'h4d,1);
        while(m_busy) begin
            step(0,0,8'hb2,0);
            if(m_busy && (m_t%5)==2) pulse_reset;
        end
        step(0,0,8'h00,0); pulse_reset;
        step(0,0,8'h00,0); pulse_reset;
        step(0,0,8'h00,1);
        // Seeded random legal traffic, including one synchronous reset.
        guard=0;
        while(random_transfers<12 && guard<6000) begin
            seed=advance(seed);
            next_slave=seed[23:16];
            step(guard==733,seed[0]|seed[1],seed[15:8],seed[2]|seed[3]);
            if(last_accept) random_transfers=random_transfers+1;
            guard=guard+1;
        end
        finish_transfer(0);
        step(0,0,8'h00,1);
        if(m_busy || m_rsp_valid || accepted != retired+aborted_busy+aborted_rsp)
            checker_fail("final_drain_conservation");
        if(directed!=6 || random_transfers<12 || aborted_busy<FRAME || aborted_rsp<3 ||
           stalled_rsp<19 ||blocked_cmd<FRAME || pulses<4)
            coverage_fail("required_transfer_reset_pulse_coverage");
        $display("COVERAGE case=%0d HALF=%0d steps=%0d accepted=%0d retired=%0d aborted_busy=%0d aborted_rsp=%0d stalled_rsp=%0d blocked=%0d pulses=%0d random=%0d",
            CASE_ID,HALF,checked,accepted,retired,aborted_busy,aborted_rsp,stalled_rsp,blocked_cmd,pulses,random_transfers);
        error_count=errors;
        failed=(errors!=0);
        finished=1;
    end
endmodule

module spi_master_tb;
    reg clk=0;
    wire [3:0] finished, failed;
    wire [31:0] errors0, errors1, errors2, errors3;
    always #5 clk=~clk;
    spi_master_case #(.HALF(2),.USE_TOP(1),.CASE_ID(0)) default_case(clk,finished[0],failed[0],errors0);
    spi_master_case #(.HALF(1),.CASE_ID(1)) half1_case(clk,finished[1],failed[1],errors1);
    spi_master_case #(.HALF(3),.CASE_ID(2)) half3_case(clk,finished[2],failed[2],errors2);
    spi_master_case #(.HALF(8),.CASE_ID(3)) half8_case(clk,finished[3],failed[3],errors3);
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
