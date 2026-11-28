`timescale 1ns/1ps
// Independent checker for the iterative CORDIC sine/cosine core. Two references:
// (1) a bit-exact model of the contract written here with 32-bit integers
// (quadrant fold by half a turn, start x = +-39797, sixteen micro-rotations with
// arithmetic shifts, the same arctangent table, z >= 0 rotates up, Q2.16 to
// Q2.14 with round half up), compared exactly on every result; and (2) a loose
// check of every result against cos and sin from real-valued Taylor series,
// within 4 Q2.14 LSB, which catches a table or gain error shared by the design
// and model (1). The table and gain are also checked against real arctangents
// at time 0. Angles: quadrant and octant boundaries, a full sweep at a stride of
// 61 and seeded random angles, under random valid gaps, output backpressure,
// resets and off-edge reset pulses. The handshake is checked before every rising
// edge against a cycle model (16 busy edges per angle, one in flight).
// Stimulus never depends on DUT outputs and the checker never reads internals.
module cordic_sincos_tb;
    reg clk=0, rst=1, in_valid=0, out_ready=0;
    reg [15:0] angle=0;
    wire in_ready, out_valid;
    wire [15:0] cos_out, sin_out;
    cordic_sincos dut(.clk(clk),.rst(rst),.angle(angle),.in_valid(in_valid),.in_ready(in_ready),
        .out_valid(out_valid),.out_ready(out_ready),.cos_out(cos_out),.sin_out(sin_out));
    always #5 clk=~clk;

    // Reference handshake state.
    reg m_busy=0, m_ov=0;
    integer m_cnt=0;
    reg [31:0] m_exp=0;
    reg [15:0] m_angle=0;
    // Master: an offer that is not accepted is held with its angle.
    reg hold=0, acc=0, started=0;
    reg [15:0] hangle=0, nangle=0;
    integer cycle=0, errors=0, i, offered=0;
    integer accepted=0, transfers=0, stalls=0, busy_offers=0, back_to_back=0, noise=0;
    integer busy_resets=0, ov_resets=0, pulses=0, last_transfer=-10, loose_checked=0;
    integer quadrant_hits [0:3];
    real worst=0.0;
    reg [31:0] seed=32'h0badc0de;

    task fail;
        input [511:0] rule;
        begin
            errors=errors+1;
            if(errors<=40) $display("FAIL BEHAVIOR rule=%0s cycle=%0d angle=%h",rule,cycle,m_angle);
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

    function integer atan_t;
        input integer k;
        begin
            case(k)
                0: atan_t=131072;  1: atan_t=77376;  2: atan_t=40884;  3: atan_t=20753;
                4: atan_t=10417;   5: atan_t=5213;   6: atan_t=2607;   7: atan_t=1304;
                8: atan_t=652;     9: atan_t=326;    10: atan_t=163;   11: atan_t=81;
                12: atan_t=41;     13: atan_t=20;    14: atan_t=10;    default: atan_t=5;
            endcase
        end
    endfunction
    // Wrap to an n-bit two's complement value.
    function integer wrap;
        input integer v, bits;
        integer m;
        begin
            m=v & ((1<<bits)-1);
            wrap=(m >= (1<<(bits-1))) ? m-(1<<bits) : m;
        end
    endfunction
    // {cos_out, sin_out} of the contract, bit exact.
    function [31:0] cordic_ref;
        input [15:0] a;
        integer x, y, z, xs, ys, k, c, s;
        begin
            x=39797; z=a;
            if(a[15]!=a[14]) begin x=-39797; z=a^16'h8000; end
            z=wrap(z,16)*16; y=0;
            for(k=0;k<16;k=k+1) begin
                xs=x>>>k; ys=y>>>k;
                if(z>=0) begin x=wrap(x-ys,18); y=wrap(y+xs,18); z=wrap(z-atan_t(k),20); end
                else begin x=wrap(x+ys,18); y=wrap(y-xs,18); z=wrap(z+atan_t(k),20); end
            end
            c=(x+2)>>>2; s=(y+2)>>>2;
            cordic_ref={c[15:0],s[15:0]};
        end
    endfunction

    // Real-valued references: Taylor series (no system math functions).
    function real rsin;
        input real t;
        real term, sum;
        integer k;
        begin
            term=t; sum=t;
            for(k=1;k<24;k=k+1) begin term=-term*t*t/((2.0*k)*(2.0*k+1.0)); sum=sum+term; end
            rsin=sum;
        end
    endfunction
    function real rcos;
        input real t;
        real term, sum;
        integer k;
        begin
            term=1.0; sum=1.0;
            for(k=1;k<24;k=k+1) begin term=-term*t*t/((2.0*k-1.0)*(2.0*k)); sum=sum+term; end
            rcos=sum;
        end
    endfunction
    function real ratan;
        input real t;
        real term, sum;
        integer k;
        begin
            term=t; sum=t;
            for(k=1;k<60;k=k+1) begin term=-term*t*t; sum=sum+term/(2.0*k+1.0); end
            ratan=sum;
        end
    endfunction
    real pi;

    task self_check;
        real v, prod, lo, hi;
        integer k;
        begin
            pi=16.0*ratan(0.2)-4.0*ratan(1.0/239.0);
            if(pi<3.14159265 || pi>3.14159266) checker_fail("machin_pi");
            for(k=0;k<16;k=k+1) begin
                v=(k==0 ? pi/4.0 : ratan(1.0/(1<<k)))/(2.0*pi)*1048576.0;
                if($rtoi(v+0.5)!=atan_t(k)) checker_fail("arctangent_table_rounding");
            end
            prod=1.0;
            for(k=0;k<16;k=k+1) prod=prod/(1.0+1.0/((1<<k)*(1<<k)*1.0));
            lo=(39796.5/65536.0)*(39796.5/65536.0); hi=(39797.5/65536.0)*(39797.5/65536.0);
            if(prod<lo || prod>=hi) checker_fail("gain_constant_rounding");
        end
    endtask

    function integer s16;
        input [15:0] v;
        s16=v[15] ? v-65536 : v;
    endfunction
    task loose_check;
        real th, ec, es;
        begin
            th=s16(m_angle)*2.0*pi/65536.0;
            ec=s16(cos_out)-16384.0*rcos(th); es=s16(sin_out)-16384.0*rsin(th);
            if(ec<0) ec=-ec;
            if(es<0) es=-es;
            if(ec>worst) worst=ec;
            if(es>worst) worst=es;
            if(ec>4.0 || es>4.0) fail("result_within_4_lsb_of_true_cos_and_sin");
            loose_checked=loose_checked+1;
        end
    endtask

    task check_ports;
        begin
            if(in_ready !== (!m_busy && !m_ov)) fail("in_ready_only_when_idle");
            if(out_valid !== m_ov) fail("out_valid_sixteen_edges_after_accept_until_transfer");
            if(m_ov) begin
                if(cos_out !== m_exp[31:16]) fail("cos_out_bit_exact");
                if(sin_out !== m_exp[15:0]) fail("sin_out_bit_exact");
                if(out_ready) loose_check;
            end
        end
    endtask

    // One cycle. Inputs change at the falling edge, ports are checked before
    // the rising edge. A held offer keeps in_valid and angle.
    task step;
        input r, iv;
        input [15:0] a;
        input ordy, pulse;
        begin
            @(negedge clk);
            rst=r; out_ready=ordy;
            if(hold && !r) begin in_valid=1; angle=hangle; end
            else begin in_valid=iv; angle=a; end
            if(!in_valid) noise=noise+1;
            #1; if(started) check_ports;
            if(pulse) begin #1 rst=1; #2 rst=0; pulses=pulses+1; end
            @(posedge clk);
            cycle=cycle+1;
            acc=!rst && in_valid && !m_busy && !m_ov;
            hold=!rst && in_valid && !acc; hangle=angle;
            if(rst) begin
                if(m_busy) busy_resets=busy_resets+1;
                if(m_ov) ov_resets=ov_resets+1;
                m_busy=0; m_ov=0; m_cnt=0;
                started=1;
            end else if(m_busy) begin
                if(in_valid) busy_offers=busy_offers+1;
                m_cnt=m_cnt-1;
                if(m_cnt==0) begin m_busy=0; m_ov=1; end
            end else if(m_ov) begin
                if(!out_ready) stalls=stalls+1;
                else begin m_ov=0; transfers=transfers+1; last_transfer=cycle; end
            end else if(in_valid) begin
                if(cycle==last_transfer+1) back_to_back=back_to_back+1;
                m_busy=1; m_cnt=16; accepted=accepted+1;
                m_angle=angle; m_exp=cordic_ref(angle);
                quadrant_hits[angle[15:14]]=quadrant_hits[angle[15:14]]+1;
            end
        end
    endtask

    // Angle sequence: 24 boundary angles, a stride-61 sweep of the circle, then random.
    task next_angle;
        begin
            case(offered)
                0: nangle=16'h0000;  1: nangle=16'h4000;  2: nangle=16'h8000;  3: nangle=16'hc000;
                4: nangle=16'h3fff;  5: nangle=16'h4001;  6: nangle=16'h7fff;  7: nangle=16'h8001;
                8: nangle=16'hbfff;  9: nangle=16'hc001;  10: nangle=16'hffff; 11: nangle=16'h0001;
                12: nangle=16'h2000; 13: nangle=16'h6000; 14: nangle=16'ha000; 15: nangle=16'he000;
                16: nangle=16'h1555; 17: nangle=16'h2aab; 18: nangle=16'h5555; 19: nangle=16'hd555;
                20: nangle=16'h0400; 21: nangle=16'hfc00; 22: nangle=16'h7c00; 23: nangle=16'h8400;
                default: begin
                    if(offered<24+1075) nangle=(offered-24)*61;
                    else begin seed=advance(seed); nangle=seed[23:8]; end
                end
            endcase
            offered=offered+1;
        end
    endtask

    task traffic;
        input integer cycles, valid_pct, ready_pct;
        input integer reset_at, pulse_at;
        reg iv, ordy;
        integer c;
        begin
            for(c=0;c<cycles;c=c+1) begin
                seed=advance(seed);
                iv=0;
                if(!hold && (seed%100)<valid_pct) begin iv=1; next_angle; end
                ordy=((seed>>8)%100)<ready_pct;
                if(iv) step(c==reset_at, 1, nangle, ordy, c==pulse_at);
                else step(c==reset_at, 0, seed[31:16], ordy, c==pulse_at);
            end
        end
    endtask

    initial begin
        for(i=0;i<4;i=i+1) quadrant_hits[i]=0;
        self_check;
        for(i=0;i<3;i=i+1) step(1,0,16'd0,0,0);
        // Boundary angles and the sweep at full rate, then random traffic.
        traffic(20000,100,100,-1,-1);
        traffic(4000,60,50,1777,401);
        traffic(4000,100,30,-1,2203);
        traffic(3000,40,90,-1,-1);
        for(i=0;i<200 && !m_ov;i=i+1) step(0,0,16'd0,0,0);
        step(1,0,16'd0,0,0);
        traffic(2000,100,80,-1,-1);
        for(i=0;i<40;i=i+1) step(0,0,16'd0,1,0);
        if(m_busy || m_ov || hold) checker_fail("final_drain");
        if(accepted<1300 || transfers<1290 || offered<24+1075+100 || loose_checked<1290) coverage_fail("angles");
        for(i=0;i<4;i=i+1) if(quadrant_hits[i]<200) coverage_fail("every_quadrant");
        if(stalls<300 || busy_offers<5000 || back_to_back<500 || noise<300) coverage_fail("handshake");
        if(busy_resets<1 || ov_resets<1 || pulses!=2) coverage_fail("resets");
        $display("COVERAGE cycles=%0d accepted=%0d transfers=%0d loose_checked=%0d worst_lsb=%f stalls=%0d busy_offers=%0d back_to_back=%0d noise=%0d busy_resets=%0d ov_resets=%0d pulses=%0d",
            cycle,accepted,transfers,loose_checked,worst,stalls,busy_offers,back_to_back,noise,busy_resets,ov_resets,pulses);
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
