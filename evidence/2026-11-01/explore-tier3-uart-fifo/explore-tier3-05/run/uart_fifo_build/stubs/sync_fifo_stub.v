module sync_fifo #( parameter DEPTH = 16, parameter WIDTH = 8 ) (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [7:0] out_data
);
endmodule
