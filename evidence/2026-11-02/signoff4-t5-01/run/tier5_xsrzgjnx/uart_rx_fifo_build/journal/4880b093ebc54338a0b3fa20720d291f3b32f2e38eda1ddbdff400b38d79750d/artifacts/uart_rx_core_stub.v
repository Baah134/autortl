module uart_rx_core #( parameter OVERSAMPLE_DIV = 2 ) (
    input wire clk,
    input wire rst,
    input wire rx,
    output wire [7:0] rx_data,
    output wire rx_strobe,
    output wire frame_err
);
endmodule
