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

    localparam integer BIT_TICKS = 16 * OVERSAMPLE_DIV;
    localparam [1:0] IDLE      = 2'd0,
                     BUSY      = 2'd1,
                     WAIT_IDLE = 2'd2;

    reg sync1;
    reg sync2;

    reg [1:0] state;
    reg [13:0] frame_count;
    reg vote1;
    reg vote2;
    reg [7:0] rx_shift;
    reg [7:0] rx_data_reg;
    reg rx_strobe_reg;
    reg frame_err_reg;

    wire [13:0] next_offset = frame_count + 14'd1;
    wire [13:0] bit_index = next_offset / BIT_TICKS;
    wire [13:0] bit_phase = next_offset % BIT_TICKS;
    wire majority_vote = (vote1 & vote2) |
                         (vote1 & sync2) |
                         (vote2 & sync2);

    assign rx_data = rx_data_reg;
    assign rx_strobe = rx_strobe_reg;
    assign frame_err = frame_err_reg;

    always @(posedge clk) begin
        if (rst) begin
            sync1 <= 1'b1;
            sync2 <= 1'b1;
        end else begin
            sync1 <= rx;
            sync2 <= sync1;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            state         <= IDLE;
            frame_count   <= 14'd0;
            vote1         <= 1'b0;
            vote2         <= 1'b0;
            rx_shift      <= 8'd0;
            rx_data_reg   <= 8'd0;
            rx_strobe_reg <= 1'b0;
            frame_err_reg <= 1'b0;
        end else begin
            rx_strobe_reg <= 1'b0;
            frame_err_reg <= 1'b0;

            case (state)
                IDLE: begin
                    frame_count <= 14'd0;
                    if (!sync2) begin
                        state       <= BUSY;
                        frame_count <= 14'd0;
                        rx_shift    <= 8'd0;
                    end
                end

                BUSY: begin
                    frame_count <= next_offset;

                    if (bit_phase == (7 * OVERSAMPLE_DIV))
                        vote1 <= sync2;

                    if (bit_phase == (8 * OVERSAMPLE_DIV))
                        vote2 <= sync2;

                    if (bit_phase == (9 * OVERSAMPLE_DIV)) begin
                        if (bit_index == 14'd0) begin
                            if (majority_vote)
                                state <= IDLE;
                        end else if (bit_index <= 14'd8) begin
                            rx_shift[bit_index - 1'b1] <= majority_vote;
                        end else if (bit_index == 14'd9) begin
                            if (majority_vote) begin
                                rx_data_reg   <= rx_shift;
                                rx_strobe_reg <= 1'b1;
                                state         <= IDLE;
                            end else begin
                                frame_err_reg <= 1'b1;
                                state         <= WAIT_IDLE;
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
                end
            endcase
        end
    end

endmodule