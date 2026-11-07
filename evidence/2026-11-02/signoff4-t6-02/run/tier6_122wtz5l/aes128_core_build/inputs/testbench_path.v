`timescale 1ns/1ps
// Independent checker for the iterative AES-128 encryption core. Its reference
// is a behavioral FIPS-197 cipher written here: the S-box is computed at time 0
// from the GF(2^8) inverse and affine map (no table is shared with the design),
// the key schedule follows FIPS-197 section 5.2 and MixColumns uses a general
// GF(2^8) multiply. The reference is itself checked against FIPS-197 Appendix
// B and C.1 and AESAVS known answers, and those known-answer blocks are sent to
// the DUT and compared with the published ciphertext directly. It then runs
// seeded random keys and plaintexts back to back under random valid gaps,
// output backpressure and resets, checking in_ready, out_valid and ct before
// every rising edge against a cycle model of the contract (11 busy edges per
// block, one block in flight, the next accepted after the output transfer).
// Stimulus never depends on DUT outputs and the checker never reads internals.
module aes128_core_tb;
    reg clk=0, rst=1, in_valid=0, out_ready=0;
    reg [127:0] key=0, pt=0;
    wire in_ready, out_valid;
    wire [127:0] ct;
    aes128_core dut(.clk(clk),.rst(rst),.in_valid(in_valid),.in_ready(in_ready),.key(key),.pt(pt),
        .out_valid(out_valid),.out_ready(out_ready),.ct(ct));
    always #5 clk=~clk;

    reg [7:0] sb [0:255];
    reg [127:0] kat_k [0:14];
    reg [127:0] kat_p [0:14];
    reg [127:0] kat_c [0:14];
    // Reference handshake state: one block in flight.
    reg m_busy=0, m_ov=0;
    integer m_cnt=0;
    reg [127:0] m_ct=0, m_exp=0;
    reg m_kat=0;
    // Master: an offer that is not accepted is held with its payload.
    reg hold=0, offer_kat=0, acc=0, started=0;
    reg [127:0] hkey=0, hpt=0, offer_exp=0, nkey=0, npt=0;
    integer cycle=0, errors=0, i, j, n, offered=0;
    integer accepted=0, transfers=0, kat_ok=0, stalls=0, busy_offers=0, back_to_back=0, noise=0;
    integer busy_resets=0, ov_resets=0, pulses=0, last_transfer=-10;
    reg [31:0] seed=32'h1f123bb5;

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

    // GF(2^8) multiply modulo x^8 + x^4 + x^3 + x + 1.
    function [7:0] gm;
        input [7:0] a, b;
        reg [7:0] p, aa, bb;
        integer k;
        begin
            p=0; aa=a; bb=b;
            for(k=0;k<8;k=k+1) begin
                if(bb[0]) p=p^aa;
                aa=aa[7] ? ((aa<<1)^8'h1b) : (aa<<1);
                bb=bb>>1;
            end
            gm=p;
        end
    endfunction
    function [7:0] rotl8;
        input [7:0] a;
        input integer s;
        rotl8=(a<<s)|(a>>(8-s));
    endfunction
    task build_sbox;
        reg [7:0] inv, p;
        integer v, k;
        begin
            for(v=0;v<256;v=v+1) begin
                // inverse = v^254 by square and multiply (0 maps to 0)
                inv=1; p=v;
                for(k=0;k<8;k=k+1) begin
                    if(k!=0) inv=gm(inv,p);
                    p=gm(p,p);
                end
                if(v==0) inv=0;
                sb[v]=inv^rotl8(inv,1)^rotl8(inv,2)^rotl8(inv,3)^rotl8(inv,4)^8'h63;
            end
        end
    endtask

    function [127:0] sub_bytes;
        input [127:0] s;
        integer k;
        begin for(k=0;k<16;k=k+1) sub_bytes[127-8*k -: 8]=sb[s[127-8*k -: 8]]; end
    endfunction
    // Byte k is row k%4, column k/4; row r rotates left by r.
    function [127:0] shift_rows;
        input [127:0] s;
        integer r, c;
        begin
            for(r=0;r<4;r=r+1)
                for(c=0;c<4;c=c+1)
                    shift_rows[127-8*(r+4*c) -: 8]=s[127-8*(r+4*((c+r)%4)) -: 8];
        end
    endfunction
    function [127:0] mix_columns;
        input [127:0] s;
        reg [7:0] a0, a1, a2, a3;
        integer c;
        begin
            for(c=0;c<4;c=c+1) begin
                a0=s[127-32*c -: 8]; a1=s[119-32*c -: 8]; a2=s[111-32*c -: 8]; a3=s[103-32*c -: 8];
                mix_columns[127-32*c -: 8]=gm(8'h02,a0)^gm(8'h03,a1)^a2^a3;
                mix_columns[119-32*c -: 8]=a0^gm(8'h02,a1)^gm(8'h03,a2)^a3;
                mix_columns[111-32*c -: 8]=a0^a1^gm(8'h02,a2)^gm(8'h03,a3);
                mix_columns[103-32*c -: 8]=gm(8'h03,a0)^a1^a2^gm(8'h02,a3);
            end
        end
    endfunction
    function [127:0] aes_ref;
        input [127:0] k, p;
        reg [127:0] s, rk;
        reg [31:0] w0, w1, w2, w3, t;
        reg [7:0] rc;
        integer r;
        begin
            s=p^k; rk=k; rc=8'h01;
            for(r=1;r<=10;r=r+1) begin
                w0=rk[127:96]; w1=rk[95:64]; w2=rk[63:32]; w3=rk[31:0];
                t={sb[w3[23:16]]^rc, sb[w3[15:8]], sb[w3[7:0]], sb[w3[31:24]]};
                w0=w0^t; w1=w1^w0; w2=w2^w1; w3=w3^w2;
                rk={w0,w1,w2,w3};
                rc=gm(rc,8'h02);
                s=shift_rows(sub_bytes(s));
                if(r<10) s=mix_columns(s);
                s=s^rk;
            end
            aes_ref=s;
        end
    endfunction

    task check_ports;
        begin
            if(in_ready !== (!m_busy && !m_ov)) fail("in_ready_only_when_idle");
            if(out_valid !== m_ov) fail("out_valid_eleven_edges_after_accept_until_transfer");
            if(m_ov && ct !== m_ct) begin
                if(m_kat) fail("ciphertext_matches_published_known_answer");
                else fail("ciphertext_matches_reference_cipher");
            end
        end
    endtask

    // One cycle. Inputs change at the falling edge and the ports are checked
    // before the rising edge. A held offer keeps in_valid, key and pt.
    task step;
        input r, iv;
        input [127:0] k, p;
        input ordy, pulse;
        begin
            @(negedge clk);
            rst=r; out_ready=ordy;
            if(hold && !r) begin in_valid=1; key=hkey; pt=hpt; end
            else begin in_valid=iv; key=k; pt=p; end
            if(!in_valid) noise=noise+1;
            #1; if(started) check_ports;
            if(pulse) begin #1 rst=1; #2 rst=0; pulses=pulses+1; end
            @(posedge clk);
            cycle=cycle+1;
            acc=!rst && in_valid && !m_busy && !m_ov;
            hold=!rst && in_valid && !acc; hkey=key; hpt=pt;
            if(rst) begin
                if(m_busy) busy_resets=busy_resets+1;
                if(m_ov) ov_resets=ov_resets+1;
                m_busy=0; m_ov=0; m_cnt=0;
                started=1;
            end else if(m_busy) begin
                if(in_valid) busy_offers=busy_offers+1;
                m_cnt=m_cnt-1;
                if(m_cnt==0) begin m_busy=0; m_ov=1; m_ct=m_exp; end
            end else if(m_ov) begin
                if(!out_ready) stalls=stalls+1;
                else begin
                    m_ov=0; transfers=transfers+1; last_transfer=cycle;
                    if(m_kat) kat_ok=kat_ok+1;
                end
            end else if(in_valid) begin
                if(cycle==last_transfer+1) back_to_back=back_to_back+1;
                m_busy=1; m_cnt=11; accepted=accepted+1;
                m_exp=aes_ref(key,pt); m_kat=offer_kat;
                if(offer_kat) begin
                    if(m_exp!==offer_exp) checker_fail("reference_cipher_matches_known_answer");
                    m_exp=offer_exp;
                end
            end
        end
    endtask

    // Offer the next block when no offer is held: known answers first, then
    // seeded random keys and plaintexts.
    task next_block;
        begin
            offer_kat=0;
            if(offered<15) begin
                nkey=kat_k[offered]; npt=kat_p[offered]; offer_exp=kat_c[offered]; offer_kat=1;
            end else begin
                for(j=0;j<4;j=j+1) begin
                    seed=advance(seed); nkey[127-32*j -: 32]=seed;
                    seed=advance(seed); npt[127-32*j -: 32]=seed;
                end
                if(offered%97==20) nkey=0;
                if(offered%89==30) npt={128{1'b1}};
            end
            offered=offered+1;
        end
    endtask

    task traffic;
        input integer cycles, valid_pct, ready_pct;
        input integer reset_at, pulse_at;
        reg iv, ordy;
        reg [127:0] junk_k, junk_p;
        integer c;
        begin
            for(c=0;c<cycles;c=c+1) begin
                seed=advance(seed);
                iv=0;
                if(!hold && (seed%100)<valid_pct) begin iv=1; next_block; end
                ordy=((seed>>8)%100)<ready_pct;
                junk_k={4{advance(seed^32'h55aa)}}; junk_p={4{advance(seed^32'h1234)}};
                if(iv) step(c==reset_at, 1, nkey, npt, ordy, c==pulse_at);
                else step(c==reset_at, 0, junk_k, junk_p, ordy, c==pulse_at);
            end
        end
    endtask

    initial begin
        build_sbox;
        if(sb[8'h00]!==8'h63 || sb[8'h01]!==8'h7c || sb[8'h53]!==8'hed || sb[8'hff]!==8'h16)
            checker_fail("sbox_known_entries");
        // FIPS-197 C.1 and Appendix B, then AESAVS GFSbox, KeySbox, VarTxt and VarKey answers.
        kat_k[0]=128'h000102030405060708090a0b0c0d0e0f; kat_p[0]=128'h00112233445566778899aabbccddeeff; kat_c[0]=128'h69c4e0d86a7b0430d8cdb78070b4c55a;
        kat_k[1]=128'h2b7e151628aed2a6abf7158809cf4f3c; kat_p[1]=128'h3243f6a8885a308d313198a2e0370734; kat_c[1]=128'h3925841d02dc09fbdc118597196a0b32;
        kat_k[2]=128'h0; kat_p[2]=128'hf34481ec3cc627bacd5dc3fb08f273e6; kat_c[2]=128'h0336763e966d92595a567cc9ce537f5e;
        kat_k[3]=128'h0; kat_p[3]=128'h9798c4640bad75c7c3227db910174e72; kat_c[3]=128'ha9a1631bf4996954ebc093957b234589;
        kat_k[4]=128'h0; kat_p[4]=128'h96ab5c2ff612d9dfaae8c31f30c42168; kat_c[4]=128'hff4f8391a6a40ca5b25d23bedd44a597;
        kat_k[5]=128'h0; kat_p[5]=128'h6a118a874519e64e9963798a503f1d35; kat_c[5]=128'hdc43be40be0e53712f7e2bf5ca707209;
        kat_k[6]=128'h0; kat_p[6]=128'hcb9fceec81286ca3e989bd979b0cb284; kat_c[6]=128'h92beedab1895a94faa69b632e5cc47ce;
        kat_k[7]=128'h0; kat_p[7]=128'hb26aeb1874e47ca8358ff22378f09144; kat_c[7]=128'h459264f4798f6a78bacb89c15ed3d601;
        kat_k[8]=128'h0; kat_p[8]=128'h58c8e00b2631686d54eab84b91f0aca1; kat_c[8]=128'h08a4e2efec8a8e3312ca7460b9040bbf;
        kat_k[9]=128'h10a58869d74be5a374cf867cfb473859; kat_p[9]=128'h0; kat_c[9]=128'h6d251e6944b051e04eaa6fb4dbf78465;
        kat_k[10]=128'h0; kat_p[10]=128'h80000000000000000000000000000000; kat_c[10]=128'h3ad78e726c1ec02b7ebfe92b23d9ec34;
        kat_k[11]=128'h80000000000000000000000000000000; kat_p[11]=128'h0; kat_c[11]=128'h0edd33d3c621e546455bd8ba1418bec8;
        kat_k[12]=128'h0; kat_p[12]=128'h0; kat_c[12]=128'h66e94bd4ef8a2c3b884cfa59ca342b2e;
        kat_k[13]=128'hffffffffffffffffffffffffffffffff; kat_p[13]=128'h0; kat_c[13]=128'ha1f6258c877d5fcd8964484538bfc92c;
        kat_k[14]=128'h0; kat_p[14]=128'hffffffffffffffffffffffffffffffff; kat_c[14]=128'h3f5b8cc9ea855a0afa7347d23e8d664e;
        for(i=0;i<15;i=i+1)
            if(aes_ref(kat_k[i],kat_p[i])!==kat_c[i]) checker_fail("reference_cipher_known_answers");
        // Reset, then known answers at full rate with output always ready.
        for(i=0;i<3;i=i+1) step(1,0,128'd0,128'd0,0,0);
        traffic(250,100,100,-1,-1);
        // Random traffic: gaps, backpressure, a reset mid-block, a reset with
        // an output pending, and two off-edge reset pulses.
        traffic(2000,70,60,777,401);
        traffic(2000,100,30,-1,1203);
        traffic(1500,40,90,-1,-1);
        // Reset while an output waits: find a cycle with the result pending.
        for(i=0;i<200 && !(m_ov);i=i+1) step(0,0,128'd0,128'd0,0,0);
        step(1,0,128'd0,128'd0,0,0);
        traffic(1500,100,80,-1,-1);
        for(i=0;i<30;i=i+1) step(0,0,128'd0,128'd0,1,0);
        if(m_busy || m_ov || hold) checker_fail("final_drain");
        if(kat_ok<15) coverage_fail("known_answers_transferred");
        if(accepted<400 || transfers<390) coverage_fail("blocks");
        if(stalls<200 || busy_offers<1000 || back_to_back<100 || noise<200) coverage_fail("handshake");
        if(busy_resets<1 || ov_resets<1 || pulses!=2) coverage_fail("resets");
        $display("COVERAGE cycles=%0d accepted=%0d transfers=%0d known_answers=%0d stalls=%0d busy_offers=%0d back_to_back=%0d noise=%0d busy_resets=%0d ov_resets=%0d pulses=%0d",
            cycle,accepted,transfers,kat_ok,stalls,busy_offers,back_to_back,noise,busy_resets,ov_resets,pulses);
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
