module uart_tx_core #( parameter DIV = 868 ) (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire tx
);
endmodule
