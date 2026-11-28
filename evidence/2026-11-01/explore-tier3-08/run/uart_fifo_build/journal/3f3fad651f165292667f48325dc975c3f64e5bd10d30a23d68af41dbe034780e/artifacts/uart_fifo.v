`timescale 1ns/1ps
// @latency 1
module byte_fifo #(
    parameter DEPTH = 8
) (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);

    localparam integer COUNT_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH + 1);

    reg [7:0] mem [0:DEPTH-1];
    integer read_ptr;
    integer write_ptr;
    reg [COUNT_WIDTH-1:0] occupancy;

    assign in_ready = (occupancy < DEPTH);
    assign out_valid = (occupancy > 0);
    assign out_data = (occupancy > 0) ? mem[read_ptr] : 8'b0;

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 0;
            write_ptr <= 0;
            occupancy <= 0;
        end else begin
            if (in_valid && in_ready) begin
                mem[write_ptr] <= in_data;
                if (write_ptr == DEPTH - 1)
                    write_ptr <= 0;
                else
                    write_ptr <= write_ptr + 1;
            end

            if (out_valid && out_ready) begin
                if (read_ptr == DEPTH - 1)
                    read_ptr <= 0;
                else
                    read_ptr <= read_ptr + 1;
            end

            if ((in_valid && in_ready) && !(out_valid && out_ready))
                occupancy <= occupancy + 1'b1;
            else if (!(in_valid && in_ready) && (out_valid && out_ready))
                occupancy <= occupancy - 1'b1;
        end
    end

endmodule

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
                (state == DATA)  ? tx_shift[0] :
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
                            tx_shift <= {1'b0, tx_shift[7:1]};
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

`timescale 1ns/1ps
module uart_fifo (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire tx
);
    wire [7:0] w_byte_fifo_out_data;
    wire w_byte_fifo_out_valid;
    wire w_uart_tx_tx_ready;

    byte_fifo #(.DEPTH(8)) u_byte_fifo (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(w_byte_fifo_out_data),
        .out_valid(w_byte_fifo_out_valid),
        .out_ready(w_uart_tx_tx_ready)
    );

    uart_tx #(.CLKS_PER_BIT(16)) u_uart_tx (
        .clk(clk),
        .rst(rst),
        .tx_data(w_byte_fifo_out_data),
        .tx_valid(w_byte_fifo_out_valid),
        .tx_ready(w_uart_tx_tx_ready),
        .tx(tx)
    );
endmodule