`timescale 1ns / 1ps
// Basys 3 bring-up: echoes every byte received on the USB-UART back to
// the PC and shows the last received byte on led[7:0].
// btnC is reset. A 16-byte FIFO absorbs small baud-rate differences
// between the PC and the board during back-to-back streaming.
module basys3_uart_echo #(
    parameter CLKS_PER_BIT = 868          // 100 MHz / 115200 baud
) (
    input        clk,                     // 100 MHz, pin W5
    input        btnC,
    input        RsRx,                    // from PC
    output       RsTx,                    // to PC
    output [7:0] led
);
    // Synchronize the button before using it as a synchronous reset.
    reg rst_meta = 1'b1, rst = 1'b1;
    always @(posedge clk) begin
        rst_meta <= btnC;
        rst      <= rst_meta;
    end

    wire [7:0] rx_data;
    wire       rx_valid;
    wire       rx_frame_err;

    uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_rx (
        .clk(clk), .rst(rst), .rx(RsRx),
        .data(rx_data), .valid(rx_valid), .frame_err(rx_frame_err)
    );

    wire [7:0] fifo_dout;
    wire       fifo_empty, fifo_full;
    wire       tx_busy;
    wire       tx_start = !tx_busy && !fifo_empty;

    sync_fifo #(.WIDTH(8), .DEPTH_LOG2(4)) u_fifo (
        .clk(clk), .rst(rst),
        .wr_en(rx_valid), .din(rx_data),
        .rd_en(tx_start), .dout(fifo_dout),
        .empty(fifo_empty), .full(fifo_full)
    );

    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_tx (
        .clk(clk), .rst(rst),
        .start(tx_start), .data(fifo_dout),
        .tx(RsTx), .busy(tx_busy)
    );

    reg [7:0] last_byte;
    always @(posedge clk) begin
        if (rst)           last_byte <= 8'd0;
        else if (rx_valid) last_byte <= rx_data;
    end
    assign led = last_byte;
endmodule
