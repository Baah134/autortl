`timescale 1ns/1ps
// @latency 1
module uart_tx #(
    parameter integer CLKS_PER_BIT = 16
) (
    input wire clk,
    input wire rst,
    input wire [7:0] tx_data,
    input wire tx_valid,
    output wire tx_ready,
    output wire tx
);

    localparam [1:0] IDLE  = 2'd0;
    localparam [1:0] START = 2'd1;
    localparam [1:0] DATA  = 2'd2;
    localparam [1:0] STOP  = 2'd3;

    reg [1:0] state;
    reg [7:0] clk_count;
    reg [2:0] bit_index;
    reg [7:0] tx_shift;

    wire bit_period_done;
    assign bit_period_done = (clk_count == CLKS_PER_BIT - 1);

    assign tx_ready = (state == IDLE) ||
                      ((state == STOP) && bit_period_done);

    assign tx = (state == START) ? 1'b0 :
                (state == DATA)  ? tx_shift[bit_index] :
                                   1'b1;

    always @(posedge clk) begin
        if (rst) begin
            state     <= IDLE;
            clk_count <= 8'd0;
            bit_index <= 3'd0;
            tx_shift  <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    clk_count <= 8'd0;
                    if (tx_valid) begin
                        tx_shift  <= tx_data;
                        bit_index <= 3'd0;
                        state     <= START;
                    end
                end

                START: begin
                    if (bit_period_done) begin
                        clk_count <= 8'd0;
                        bit_index <= 3'd0;
                        state     <= DATA;
                    end else begin
                        clk_count <= clk_count + 1'b1;
                    end
                end

                DATA: begin
                    if (bit_period_done) begin
                        clk_count <= 8'd0;
                        if (bit_index == 3'd7) begin
                            state <= STOP;
                        end else begin
                            bit_index <= bit_index + 1'b1;
                        end
                    end else begin
                        clk_count <= clk_count + 1'b1;
                    end
                end

                STOP: begin
                    if (bit_period_done) begin
                        clk_count <= 8'd0;
                        if (tx_valid) begin
                            tx_shift  <= tx_data;
                            bit_index <= 3'd0;
                            state     <= START;
                        end else begin
                            state <= IDLE;
                        end
                    end else begin
                        clk_count <= clk_count + 1'b1;
                    end
                end

                default: begin
                    state     <= IDLE;
                    clk_count <= 8'd0;
                    bit_index <= 3'd0;
                    tx_shift  <= 8'd0;
                end
            endcase
        end
    end

endmodule