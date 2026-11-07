module sync_byte_fifo #( parameter DEPTH = 8 ) (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] data_out,
    output wire valid_out,
    input wire out_ready
);
endmodule
