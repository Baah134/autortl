`timescale 1ns/1ps
// @latency 1
module skid_buffer_core(input clk,input rst,input [7:0] in_data,
    input in_valid,output in_ready,output [7:0] out_data,
    output out_valid,input out_ready);
    assign out_valid = in_valid && !rst;
    assign in_ready = out_ready && !rst;
    assign out_data = in_data;
endmodule
