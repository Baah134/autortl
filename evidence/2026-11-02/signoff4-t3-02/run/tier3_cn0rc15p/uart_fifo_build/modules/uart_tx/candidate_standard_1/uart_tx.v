`timescale 1ns/1ps
// @latency 0
module uart_tx #(
    parameter CLKS_PER_BIT = 16
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
reg [31:0] baud_count;
reg [2:0] bit_index;
reg [7:0] data_reg;

assign tx_ready = (state == IDLE) ||
                  ((state == STOP) && (baud_count == CLKS_PER_BIT - 1));

assign tx = (state == IDLE)  ? 1'b1 :
            (state == START) ? 1'b0 :
            (state == DATA)  ? data_reg[0] :
                               1'b1;

always @(posedge clk) begin
    if (!rst) begin
        state      <= IDLE;
        baud_count <= 32'd0;
        bit_index  <= 3'd0;
        data_reg   <= 8'd0;
    end else begin
        case (state)
            IDLE: begin
                baud_count <= 32'd0;
                if (tx_valid) begin
                    data_reg <= tx_data;
                    state    <= START;
                end
            end

            START: begin
                if (baud_count == CLKS_PER_BIT - 1) begin
                    baud_count <= 32'd0;
                    bit_index  <= 3'd0;
                    state      <= DATA;
                end else begin
                    baud_count <= baud_count + 1'b1;
                end
            end

            DATA: begin
                if (baud_count == CLKS_PER_BIT - 1) begin
                    baud_count <= 32'd0;
                    data_reg   <= {1'b0, data_reg[7:1]};
                    if (bit_index == 3'd7) begin
                        state <= STOP;
                    end else begin
                        bit_index <= bit_index + 1'b1;
                    end
                end else begin
                    baud_count <= baud_count + 1'b1;
                end
            end

            STOP: begin
                if (baud_count == CLKS_PER_BIT - 1) begin
                    baud_count <= 32'd0;
                    if (tx_valid) begin
                        data_reg <= tx_data;
                        state    <= START;
                    end else begin
                        state <= IDLE;
                    end
                end else begin
                    baud_count <= baud_count + 1'b1;
                end
            end

            default: begin
                state      <= IDLE;
                baud_count <= 32'd0;
                bit_index  <= 3'd0;
                data_reg   <= 8'd0;
            end
        endcase
    end
end

endmodule