module uart_tx #( parameter DIV = 868 ) (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire tx_ready,
    input wire [7:0] in_data,
    output wire tx
);
endmodule
