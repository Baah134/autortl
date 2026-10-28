`timescale 1ns / 1ps
// Basys 3 bring-up: echoes every byte received on the USB-UART back to
// the PC and shows the last received byte on led[7:0].
// led_overflow (LD15) latches if the FIFO ever overflowed (a byte was
// dropped); led_frame_err (LD14) latches if a frame with a low stop bit
// arrived. btnC resets.
// The transmitter's short stop bit keeps the echo faster than a sender
// up to 0.6% fast, so the FIFO only absorbs short-term jitter.
module basys3_uart_echo #(
    parameter CLKS_PER_BIT = 868,         // 100 MHz / 115200 baud
    parameter FIFO_DEPTH_LOG2 = 4
) (
    input         clk,                    // 100 MHz, pin W5
    input         btnC,
    input         RsRx,                   // from PC
    output        RsTx,                   // to PC
    output [7:0]  led,
    output        led_frame_err,
    output        led_overflow
);
    // Synchronize the button before using it as a synchronous reset.
    (* ASYNC_REG = "TRUE" *) reg rst_meta = 1'b1, rst = 1'b1;
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

    sync_fifo #(.WIDTH(8), .DEPTH_LOG2(FIFO_DEPTH_LOG2)) u_fifo (
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
    reg       overflow, frame_error;
    always @(posedge clk) begin
        if (rst) begin
            last_byte   <= 8'd0;
            overflow    <= 1'b0;
            frame_error <= 1'b0;
        end else begin
            if (rx_valid)              last_byte   <= rx_data;
            if (rx_valid && fifo_full) overflow    <= 1'b1;
            if (rx_frame_err)          frame_error <= 1'b1;
        end
    end
    assign led           = last_byte;
    assign led_frame_err = frame_error;
    assign led_overflow  = overflow;
endmodule
