`timescale 1ns/1ps
// Qualification reference only; never a generation seed.
// @latency 3
module signed_fir4_core(input clk,input rst,input signed [7:0] x,
    input in_valid,output in_ready,output signed [12:0] out_data,
    output out_valid,input out_ready);
    reg signed [7:0] h1,h2,h3;
    reg v1,v2,v3;
    reg signed [12:0] pair_a,pair_b,combined,result;
    wire signed [12:0] sx={{5{x[7]}},x};
    wire signed [12:0] sh1={{5{h1[7]}},h1};
    wire signed [12:0] sh2={{5{h2[7]}},h2};
    wire signed [12:0] sh3={{5{h3[7]}},h3};
    wire r3=!v3 || out_ready;
    wire r2=!v2 || r3;
    wire r1=!v1 || r2;
    assign in_ready=r1;
    assign out_valid=v3;
    assign out_data=result;
    always @(posedge clk) begin // history_clock
        if(rst) begin
            h1<=0;h2<=0;h3<=0; // history_reset
        end else if(in_valid && in_ready) begin // history_gate
            h3<=h2;h2<=h1;h1<=x; // history_shift
        end
    end
    always @(posedge clk) begin // pipeline_clock
        if(rst) begin
            v1<=0; // reset_v1
            v2<=0; // reset_v2
            v3<=0; // reset_v3
        end else begin
            if(r3) begin // stage3_gate
                v3<=v2;
                if(v2) result<=combined; // stage3_data
            end
            if(r2) begin // stage2_gate
                v2<=v1;
                if(v1) combined<=pair_a+pair_b;
            end
            if(in_ready) begin // stage1_gate
                v1<=in_valid && !v3; // input_valid
                if(in_valid) begin
                    pair_a<=13'sd3*sx-13'sd5*sh1;
                    pair_b<=13'sd7*sh2-13'sd2*sh3;
                end
            end
        end // pipeline_normal
    end
endmodule
