`timescale 1ns/1ps
// Basys 3 echo whose receive AND transmit paths were both built by the harness.
//
//   RsRx -> uart_rx_core -> rx_fifo --valid/ready--> byte_fifo -> uart_tx -> RsTx
//           (tier5 uart_rx_fifo_build winner)        (tier3 uart_fifo_build winner)
//
// The four child modules are read unchanged from their archived winner files.
// Each winner's mechanical top fixes simulation-sized parameters, so this
// hand-written wrapper repeats the tops' wiring with board parameters instead:
// 16 x 54 = 864 clocks per bit on both sides (115,741 baud from 100 MHz; the
// PC's 115,200 is 0.47% slower, so the transmitter always keeps up). FIFO
// depths are ones the qualified testbenches exercised (ADDR_BITS 3, DEPTH 8).
// Only reset generation and the LEDs are added here.
module basys3_harness_echo (
    input  wire       clk,
    input  wire       btnC,
    input  wire       RsRx,
    output wire       RsTx,
    output wire [7:0] led
);
    // Power-on reset for 16 cycles, then btnC through a two-flop synchronizer.
    reg [3:0] por = 4'd0;
    reg [1:0] btn_sync = 2'b00;
    reg       rst = 1'b1;
    always @(posedge clk) begin
        btn_sync <= {btn_sync[0], btnC};
        if (por != 4'hF) por <= por + 4'd1;
        rst <= (por != 4'hF) | btn_sync[1];
    end

    // Receive side: the tier5 winner's children, wired as its uart_rx_fifo top.
    wire       rx_strobe, frame_err, rx_overflow;
    wire [7:0] rx_data;
    wire [7:0] stream_data;
    wire       stream_valid, stream_ready;
    wire [3:0] ferr_count, ovf_count;

    uart_rx_core #(.OVERSAMPLE_DIV(54)) u_uart_rx_core (
        .clk(clk), .rst(rst), .rx(RsRx),
        .rx_data(rx_data), .rx_strobe(rx_strobe), .frame_err(frame_err)
    );
    rx_fifo #(.ADDR_BITS(3)) u_rx_fifo (
        .clk(clk), .rst(rst), .wr_en(rx_strobe), .wr_data(rx_data),
        .out_data(stream_data), .out_valid(stream_valid), .out_ready(stream_ready),
        .overflow(rx_overflow)
    );
    rx_err_count u_rx_err_count (
        .clk(clk), .rst(rst), .ferr_in(frame_err), .ovf_in(rx_overflow),
        .ferr_count(ferr_count), .ovf_count(ovf_count)
    );

    // Transmit side: the tier3 winner's children, wired as its uart_fifo top.
    wire [7:0] tx_fifo_data;
    wire       tx_fifo_valid, tx_ready;

    byte_fifo #(.DEPTH(8)) u_byte_fifo (
        .clk(clk), .rst(rst),
        .in_data(stream_data), .in_valid(stream_valid), .in_ready(stream_ready),
        .out_data(tx_fifo_data), .out_valid(tx_fifo_valid), .out_ready(tx_ready)
    );
    uart_tx #(.CLKS_PER_BIT(864)) u_uart_tx (
        .clk(clk), .rst(rst),
        .tx_data(tx_fifo_data), .tx_valid(tx_fifo_valid), .tx_ready(tx_ready),
        .tx(RsTx)
    );

    // LD0-LD3: framing errors seen by the receiver; LD4-LD7: receive overflows.
    assign led = {ovf_count, ferr_count};
endmodule
