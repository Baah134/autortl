`timescale 1ns / 1ps
`default_nettype none
// Basys 3 echo whose transmitter was written by the harness.
//
// The PC's bytes arrive through the hand-written uart_rx used by the board's
// first echo design, are buffered in shell_fifo, and leave through
// `uart_tx`, the harness's generated top from design_spec.json, used
// unedited. So every byte the PC reads back was serialized by
// harness-generated logic driving the RsTx pin.
//
// The spec makes back-to-back frames DIV+1 cycles per stop bit, and the PC
// may send slightly fast, so sustained line-rate input slowly fills the
// FIFO. The PC test sends in chunks the FIFO absorbs. led_overflow latches
// if a byte is ever dropped, and led_frame_err if a received frame had a
// low stop bit. led[7:0] shows the last byte sent. btnC resets.
module basys3_harness_uart_tx #(
    parameter CLKS_PER_BIT = 868,         // 100 MHz / 115200 baud
    parameter FIFO_DEPTH_LOG2 = 5
) (
    input  wire       clk,                // 100 MHz, pin W5
    input  wire       btnC,
    input  wire       RsRx,               // from PC
    output wire       RsTx,               // to PC, driven by the harness's uart_tx
    output wire [7:0] led,
    output wire       led_frame_err,
    output wire       led_overflow
);
    (* ASYNC_REG = "TRUE" *) reg rst_meta = 1'b1, rst = 1'b1;
    always @(posedge clk) begin
        rst_meta <= btnC;
        rst      <= rst_meta;
    end

    wire [7:0] rx_data;
    wire       rx_valid, rx_frame_err;
    uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_rx (
        .clk(clk), .rst(rst), .rx(RsRx),
        .data(rx_data), .valid(rx_valid), .frame_err(rx_frame_err)
    );

    wire [7:0] fifo_dout;
    wire       fifo_empty, fifo_full;
    wire       tx_ready;
    wire       tx_accept = !fifo_empty && tx_ready;   // the harness TX takes the byte at this edge
    shell_fifo #(.WIDTH(8), .DEPTH_LOG2(FIFO_DEPTH_LOG2)) u_fifo (
        .clk(clk), .rst(rst),
        .wr_en(rx_valid), .din(rx_data),
        .rd_en(tx_accept), .dout(fifo_dout),
        .empty(fifo_empty), .full(fifo_full)
    );

    // Harness-generated, unedited. Its default DIV=868 is the board's baud.
    (* keep_hierarchy = "yes" *)
    uart_tx u_harness_tx (
        .clk(clk), .rst(rst),
        .in_data(fifo_dout), .in_valid(!fifo_empty),
        .in_ready(tx_ready), .tx(RsTx)
    );

    reg [7:0] last_sent;
    reg       overflow, frame_error;
    always @(posedge clk) begin
        if (rst) begin
            last_sent   <= 8'd0;
            overflow    <= 1'b0;
            frame_error <= 1'b0;
        end else begin
            if (tx_accept)             last_sent   <= fifo_dout;
            if (rx_valid && fifo_full) overflow    <= 1'b1;
            if (rx_frame_err)          frame_error <= 1'b1;
        end
    end
    assign led           = last_sent;
    assign led_frame_err = frame_error;
    assign led_overflow  = overflow;
endmodule
`default_nettype wire
