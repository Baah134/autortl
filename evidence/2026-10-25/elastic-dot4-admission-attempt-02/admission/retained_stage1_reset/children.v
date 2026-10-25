`timescale 1ns/1ps
// Admission reference only, never a generator seed.
// @latency 2
module elastic_dot4_core(
    input clk,input rst,
    input [7:0] a0,b0,a1,b1,a2,b2,a3,b3,
    input in_valid,output in_ready,
    output [17:0] out_data,output out_valid,input out_ready);
    reg v1,v2;
    reg [16:0] partial01,partial23;
    reg [17:0] result;
    wire [15:0] product0=a0*b0;
    wire [15:0] product1=a1*b1;
    wire [15:0] product2=a2*b2;
    wire [15:0] product3=a3*b3;
    wire ready2=!v2 || out_ready;
    assign in_ready=!v1 || ready2;
    assign out_valid=v2;
    assign out_data=result;
    always @(posedge clk) begin
        if(rst) begin
            if(v1) v1<=v1; else v1<=0; // reset_stage1
            v2<=0; // reset_stage2
        end else begin
            if(ready2) begin
                v2<=v1; // advance_valid
                if(v1) result<={1'b0,partial01}+{1'b0,partial23};
            end
            if(in_ready) begin // capture_gate
                v1<=in_valid; // capture_valid
                if(in_valid) begin
                    partial01<={1'b0,product0}+{1'b0,product1};
                    partial23<={1'b0,product2}+{1'b0,product3};
                end
            end // capture_end
        end // normal_end
    end
endmodule
