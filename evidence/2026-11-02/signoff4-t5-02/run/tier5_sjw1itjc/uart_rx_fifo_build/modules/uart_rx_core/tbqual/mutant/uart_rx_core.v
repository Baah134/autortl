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
    reg [9:0] phase_count;
    reg [3:0] bit_index;
    reg vote_a;
    reg vote_b;
    reg [7:0] data_bits;
    reg [7:0] rx_data_reg;
    reg rx_strobe_reg;
    reg frame_err_reg;

    wire line_sample;
    assign line_sample = sync2;

    assign rx_data = rx_data_reg;
    assign rx_strobe = rx_strobe_reg;
    assign frame_err = frame_err_reg;

    always @(posedge clk) begin
        if (rst) begin
            sync1 <= 1'b1;
            sync2 <= 1'b1;
            state <= IDLE;
            phase_count <= 10'd0;
            bit_index <= 4'd0;
            vote_a <= 1'b0;
            vote_b <= 1'b0;
            data_bits <= 8'd0;
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
                    if (!line_sample) begin
                        state <= BUSY;
                        phase_count <= 10'd0;
                        bit_index <= 4'd0;
                        vote_a <= 1'b0;
                        vote_b <= 1'b0;
                    end
                end

                BUSY: begin
                    if (phase_count != (7 * OVERSAMPLE_DIV - 1))
                        vote_a <= line_sample;

                    if (phase_count == (8 * OVERSAMPLE_DIV - 1))
                        vote_b <= line_sample;

                    if (phase_count == (9 * OVERSAMPLE_DIV - 1)) begin
                        if (bit_index == 4'd0) begin
                            if (vote_a & vote_b | vote_a & line_sample | vote_b & line_sample) begin
                                state <= IDLE;
                            end
                        end else if (bit_index >= 4'd1 && bit_index <= 4'd8) begin
                            data_bits[bit_index - 1'b1] <=
                                (vote_a & vote_b) |
                                (vote_a & line_sample) |
                                (vote_b & line_sample);
                        end else if (bit_index == 4'd9) begin
                            if ((vote_a & vote_b) |
                                (vote_a & line_sample) |
                                (vote_b & line_sample)) begin
                                rx_data_reg <= data_bits;
                                rx_strobe_reg <= 1'b1;
                                state <= IDLE;
                            end else begin
                                frame_err_reg <= 1'b1;
                                state <= WAIT_IDLE;
                            end
                        end
                    end

                    if (phase_count == BIT_CYCLES - 1) begin
                        phase_count <= 10'd0;
                        bit_index <= bit_index + 1'b1;
                    end else begin
                        phase_count <= phase_count + 1'b1;
                    end
                end

                WAIT_IDLE: begin
                    if (line_sample)
                        state <= IDLE;
                end

                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule