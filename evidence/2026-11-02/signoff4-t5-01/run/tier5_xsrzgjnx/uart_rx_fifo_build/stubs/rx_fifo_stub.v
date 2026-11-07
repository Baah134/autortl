module rx_fifo #( parameter ADDR_BITS = 2 ) (
    input wire clk,
    input wire rst,
    input wire wr_en,
    input wire [7:0] wr_data,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready,
    output wire overflow
);
endmodule
