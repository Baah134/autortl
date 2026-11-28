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

    function integer clog2;
        input integer value;
        integer i;
        begin
            clog2 = 0;
            for (i = value - 1; i > 0; i = i >> 1)
                clog2 = clog2 + 1;
        end
    endfunction

    localparam integer PTR_WIDTH = (DEPTH <= 1) ? 1 : clog2(DEPTH);

    reg [7:0] mem [0:DEPTH-1];
    reg [PTR_WIDTH-1:0] read_ptr;
    reg [PTR_WIDTH-1:0] write_ptr;
    reg read_wrap;
    reg write_wrap;
    reg fifo_full;

    wire fifo_empty;
    wire [PTR_WIDTH-1:0] write_ptr_next;
    wire write_wrap_next;
    wire enqueue;
    wire dequeue;

    assign write_ptr_next = (write_ptr == DEPTH - 1) ?
                            {PTR_WIDTH{1'b0}} : write_ptr + 1'b1;
    assign write_wrap_next = (write_ptr == DEPTH - 1) ?
                             ~write_wrap : write_wrap;

    assign fifo_empty = (read_ptr == write_ptr) &&
                        (read_wrap == write_wrap);
    assign in_ready = !fifo_full;
    assign out_valid = !fifo_empty;
    assign out_data = fifo_empty ? 8'b0 : mem[read_ptr];

    assign enqueue = in_valid && in_ready;
    assign dequeue = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            read_ptr  <= {PTR_WIDTH{1'b0}};
            write_ptr <= {PTR_WIDTH{1'b0}};
            read_wrap <= 1'b0;
            write_wrap <= 1'b0;
            fifo_full <= 1'b0;
        end else begin
            if (enqueue) begin
                mem[write_ptr] <= in_data;
                write_ptr <= write_ptr_next;
                write_wrap <= write_wrap_next;
            end

            if (dequeue) begin
                if (read_ptr == DEPTH - 1) begin
                    read_ptr <= {PTR_WIDTH{1'b0}};
                    read_wrap <= ~read_wrap;
                end else begin
                    read_ptr <= read_ptr + 1'b1;
                end
            end

            if (enqueue && !dequeue)
                fifo_full <= (write_ptr_next == read_ptr) &&
                             (write_wrap_next != read_wrap);
            else if (!enqueue && dequeue)
                fifo_full <= 1'b0;
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

    function integer clog2;
        input integer value;
        integer i;
        begin
            clog2 = 0;
            for (i = value - 1; i > 0; i = i >> 1)
                clog2 = clog2 + 1;
        end
    endfunction

    localparam integer CLK_COUNT_WIDTH =
        (CLKS_PER_BIT <= 2) ? 1 : clog2(CLKS_PER_BIT);

    localparam [1:0] IDLE  = 2'd0;
    localparam [1:0] START = 2'd1;
    localparam [1:0] DATA  = 2'd2;
    localparam [1:0] STOP  = 2'd3;

    reg [1:0] state;
    reg [CLK_COUNT_WIDTH-1:0] clk_count;
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
            clk_count <= {CLK_COUNT_WIDTH{1'b0}};
            bit_index <= 3'd0;
            tx_shift  <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    clk_count <= {CLK_COUNT_WIDTH{1'b0}};
                    if (tx_valid) begin
                        tx_shift  <= tx_data;
                        bit_index <= 3'd0;
                        state     <= START;
                    end
                end

                START: begin
                    if (bit_period_done) begin
                        clk_count <= {CLK_COUNT_WIDTH{1'b0}};
                        bit_index <= 3'd0;
                        state     <= DATA;
                    end else begin
                        clk_count <= clk_count + 1'b1;
                    end
                end

                DATA: begin
                    if (bit_period_done) begin
                        clk_count <= {CLK_COUNT_WIDTH{1'b0}};
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
                        clk_count <= {CLK_COUNT_WIDTH{1'b0}};
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
                    clk_count <= {CLK_COUNT_WIDTH{1'b0}};
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