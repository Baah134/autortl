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
    reg [13:0] frame_offset;
    reg vote_7;
    reg vote_8;
    reg [7:0] frame_data;
    reg [7:0] rx_data_reg;
    reg rx_strobe_reg;
    reg frame_err_reg;

    wire [13:0] elapsed_next;
    wire [13:0] phase_next;
    wire [13:0] bit_index;
    wire majority;

    assign elapsed_next = frame_offset + 14'd1;
    assign phase_next = elapsed_next % BIT_CYCLES;
    assign bit_index = elapsed_next / BIT_CYCLES;
    assign majority = (vote_7 & vote_8) |
                      (vote_7 & sync2) |
                      (vote_8 & sync2);

    assign rx_data = rx_data_reg;
    assign rx_strobe = rx_strobe_reg;
    assign frame_err = frame_err_reg;

    always @(posedge clk) begin
        if (rst) begin
            sync1 <= 1'b1;
            sync2 <= 1'b1;
            state <= IDLE;
            frame_offset <= 14'd0;
            vote_7 <= 1'b0;
            vote_8 <= 1'b0;
            frame_data <= 8'd0;
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
                    if (sync2 != 1'b0) begin
                        state <= BUSY;
                        frame_offset <= 14'd0;
                        frame_data <= 8'd0;
                    end
                end

                BUSY: begin
                    frame_offset <= elapsed_next;

                    if (phase_next == (7 * OVERSAMPLE_DIV))
                        vote_7 <= sync2;

                    if (phase_next == (8 * OVERSAMPLE_DIV))
                        vote_8 <= sync2;

                    if (phase_next == (9 * OVERSAMPLE_DIV)) begin
                        if (elapsed_next == (153 * OVERSAMPLE_DIV)) begin
                            if (majority) begin
                                rx_data_reg <= frame_data;
                                rx_strobe_reg <= 1'b1;
                                state <= IDLE;
                            end else begin
                                frame_err_reg <= 1'b1;
                                state <= WAIT_IDLE;
                            end
                        end else if (bit_index == 0) begin
                            if (majority)
                                state <= IDLE;
                        end else if ((bit_index >= 1) && (bit_index <= 8)) begin
                            frame_data[bit_index - 1'b1] <= majority;
                        end
                    end
                end

                WAIT_IDLE: begin
                    if (sync2 == 1'b1)
                        state <= IDLE;
                end

                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule