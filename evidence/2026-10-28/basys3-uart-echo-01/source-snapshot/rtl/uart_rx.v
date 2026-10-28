`timescale 1ns / 1ps
// 8N1 UART receiver. Samples each bit at its midpoint.
// valid pulses for one cycle when a byte with a good stop bit arrives;
// frame_err pulses instead when the stop bit is low.
module uart_rx #(
    parameter CLKS_PER_BIT = 868          // 100 MHz / 115200 baud
) (
    input            clk,
    input            rst,                 // synchronous, active high
    input            rx,                  // asynchronous serial input
    output reg [7:0] data,
    output reg       valid,
    output reg       frame_err
);
    localparam IDLE = 2'd0, START = 2'd1, DATA = 2'd2, STOP = 2'd3;

    // Two-flop synchronizer; the line idles high.
    reg rx_meta, rx_sync;
    always @(posedge clk) begin
        if (rst) begin
            rx_meta <= 1'b1;
            rx_sync <= 1'b1;
        end else begin
            rx_meta <= rx;
            rx_sync <= rx_meta;
        end
    end

    reg [1:0]  state;
    reg [15:0] cnt;
    reg [2:0]  bit_idx;
    reg [7:0]  shift;

    always @(posedge clk) begin
        valid     <= 1'b0;
        frame_err <= 1'b0;
        if (rst) begin
            state   <= IDLE;
            cnt     <= 16'd0;
            bit_idx <= 3'd0;
            shift   <= 8'd0;
            data    <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    cnt <= 16'd0;
                    if (!rx_sync) state <= START;
                end
                START: begin
                    // Re-check the start bit at its midpoint to reject glitches.
                    if (cnt == CLKS_PER_BIT / 2 - 1) begin
                        cnt     <= 16'd0;
                        bit_idx <= 3'd0;
                        state   <= rx_sync ? IDLE : DATA;
                    end else begin
                        cnt <= cnt + 16'd1;
                    end
                end
                DATA: begin
                    if (cnt == CLKS_PER_BIT - 1) begin
                        cnt   <= 16'd0;
                        shift <= {rx_sync, shift[7:1]};   // LSB first
                        if (bit_idx == 3'd7) state <= STOP;
                        else                 bit_idx <= bit_idx + 3'd1;
                    end else begin
                        cnt <= cnt + 16'd1;
                    end
                end
                STOP: begin
                    if (cnt == CLKS_PER_BIT - 1) begin
                        cnt   <= 16'd0;
                        state <= IDLE;
                        if (rx_sync) begin
                            data  <= shift;
                            valid <= 1'b1;
                        end else begin
                            frame_err <= 1'b1;
                        end
                    end else begin
                        cnt <= cnt + 16'd1;
                    end
                end
            endcase
        end
    end
endmodule
