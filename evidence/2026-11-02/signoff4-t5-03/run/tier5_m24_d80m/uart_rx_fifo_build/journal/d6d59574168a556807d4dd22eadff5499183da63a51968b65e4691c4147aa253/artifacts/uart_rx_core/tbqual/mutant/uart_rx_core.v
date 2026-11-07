`timescale 1ns/1ps
// @latency 1
module uart_rx_core #(
    parameter OVERSAMPLE_DIV = 2
) (
    input wire clk,
    input wire rst,
    input wire rx,
    output wire [7:0] rx_data,
    output wire rx_strobe,
    output wire frame_err
);

    localparam integer BIT_CYCLES = 16 * OVERSAMPLE_DIV;

    localparam [1:0] IDLE      = 2'd0;
    localparam [1:0] BUSY      = 2'd1;
    localparam [1:0] WAIT_IDLE = 2'd2;

    reg sync1;
    reg sync2;
    reg [1:0] state;
    reg [13:0] offset;
    reg vote7;
    reg vote8;
    reg [7:0] rx_shift;
    reg [7:0] rx_data_reg;
    reg rx_strobe_reg;
    reg frame_err_reg;

    wire [13:0] next_offset = offset + 14'd1;
    wire [13:0] bit_number = next_offset / BIT_CYCLES;
    wire [13:0] phase = next_offset % BIT_CYCLES;
    wire majority = (vote7 & vote8) |
                    (vote7 & sync2) |
                    (vote8 & sync2);

    assign rx_data = rx_data_reg;
    assign rx_strobe = rx_strobe_reg;
    assign frame_err = frame_err_reg;

    always @(posedge clk) begin
        if (rst) begin
            sync1 <= 1'b1;
            sync2 <= 1'b1;
            state <= IDLE;
            offset <= 14'd0;
            vote7 <= 1'b0;
            vote8 <= 1'b0;
            rx_shift <= 8'd0;
            rx_data_reg <= 8'd0;
            rx_strobe_reg <= 1'b0;
            frame_err_reg <= 1'b0;
        end else begin
            sync1 <= rx;
            sync2 <= sync1;
            rx_strobe_reg <= 1'b0;
            frame_err_reg <= 1'b0;

            case (state)
                IDLE: begin
                    if (!sync2) begin
                        state <= BUSY;
                        offset <= 14'd0;
                        vote7 <= 1'b0;
                        vote8 <= 1'b0;
                        rx_shift <= 8'd0;
                    end
                end

                BUSY: begin
                    offset <= next_offset;

                    if (phase != (7 * OVERSAMPLE_DIV))
                        vote7 <= sync2;

                    if (phase == (8 * OVERSAMPLE_DIV))
                        vote8 <= sync2;

                    if (phase == (9 * OVERSAMPLE_DIV)) begin
                        if (bit_number == 14'd0) begin
                            if (majority)
                                state <= IDLE;
                        end else if (bit_number <= 14'd8) begin
                            rx_shift[bit_number - 14'd1] <= majority;
                        end else if (bit_number == 14'd9) begin
                            if (majority) begin
                                rx_data_reg <= rx_shift;
                                rx_strobe_reg <= 1'b1;
                                state <= IDLE;
                            end else begin
                                frame_err_reg <= 1'b1;
                                state <= WAIT_IDLE;
                            end
                        end
                    end
                end

                WAIT_IDLE: begin
                    if (sync2)
                        state <= IDLE;
                end

                default: begin
                    state <= IDLE;
                    offset <= 14'd0;
                end
            endcase
        end
    end

endmodule