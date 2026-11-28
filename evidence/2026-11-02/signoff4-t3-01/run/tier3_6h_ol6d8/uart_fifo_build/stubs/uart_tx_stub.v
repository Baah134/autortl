module uart_tx #( parameter CLKS_PER_BIT = 16 ) (
    input wire clk,
    input wire rst,
    input wire [7:0] tx_data,
    input wire tx_valid,
    output wire tx_ready,
    output wire tx
);
endmodule
