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

                    if (phase == (7 * OVERSAMPLE_DIV))
                        vote7 <= sync2;

                    if (phase == (8 * OVERSAMPLE_DIV))
                        vote8 <= sync2;

                    if (phase == (9 * OVERSAMPLE_DIV)) begin
                        if (bit_number == 14'd0) begin
                            if (majority)
                                state <= IDLE;
                        end else if (bit_number <= 14'd8) begin
                            rx_shift <= {majority, rx_shift[7:1]};
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

`timescale 1ns/1ps
// @latency 1
module rx_fifo #(
    parameter ADDR_BITS = 2
) (
    input wire clk,
    input wire rst,
    input wire wr_en,
    input wire [7:0] wr_data,
    output reg [7:0] out_data,
    output wire out_valid,
    input wire out_ready,
    output reg overflow
);

    localparam integer DEPTH = (1 << ADDR_BITS);
    localparam integer COUNT_BITS = ADDR_BITS + 1;

    reg [7:0] mem [0:DEPTH-1];
    reg [ADDR_BITS-1:0] rd_ptr;
    reg [ADDR_BITS-1:0] wr_ptr;
    reg [COUNT_BITS-1:0] count;

    wire pop;
    wire push;

    assign pop = out_ready && (count != 0);
    assign push = wr_en && ((count < DEPTH) || pop);

    assign out_valid = (count != 0);

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= {ADDR_BITS{1'b0}};
            wr_ptr <= {ADDR_BITS{1'b0}};
            count <= {COUNT_BITS{1'b0}};
            out_data <= 8'b0;
            overflow <= 1'b0;
        end else begin
            overflow <= wr_en && !push;

            if (push) begin
                mem[wr_ptr] <= wr_data;
                wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop)
                rd_ptr <= rd_ptr + 1'b1;

            if (pop) begin
                if (count == 1) begin
                    if (push)
                        out_data <= wr_data;
                    else
                        out_data <= 8'b0;
                end else begin
                    out_data <= mem[rd_ptr + 1'b1];
                end
            end else if (push && (count == 0)) begin
                out_data <= wr_data;
            end

            case ({push, pop})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: count <= count;
            endcase
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
module rx_err_count (
    input wire clk,
    input wire rst,
    input wire ferr_in,
    input wire ovf_in,
    output wire [3:0] ferr_count,
    output wire [3:0] ovf_count
);

    reg [3:0] ferr_count_reg;
    reg [3:0] ovf_count_reg;

    assign ferr_count = ferr_count_reg;
    assign ovf_count = ovf_count_reg;

    always @(posedge clk) begin
        if (rst) begin
            ferr_count_reg <= 4'd0;
            ovf_count_reg  <= 4'd0;
        end else begin
            if (ferr_in && (ferr_count_reg < 4'd15))
                ferr_count_reg <= ferr_count_reg + 4'd1;
            if (ovf_in && (ovf_count_reg < 4'd15))
                ovf_count_reg <= ovf_count_reg + 4'd1;
        end
    end

endmodule

`timescale 1ns/1ps
module uart_rx_fifo (
    input wire clk,
    input wire rst,
    input wire rx,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready,
    output wire frame_err,
    output wire [3:0] ferr_count,
    output wire [3:0] ovf_count
);

    wire w_uart_rx_core_rx_strobe;
    wire [7:0] w_uart_rx_core_rx_data;
    wire w_uart_rx_core_frame_err;
    wire w_rx_fifo_overflow;

    assign frame_err = w_uart_rx_core_frame_err;

    uart_rx_core #(.OVERSAMPLE_DIV(2)) u_uart_rx_core (
        .clk(clk),
        .rst(rst),
        .rx(rx),
        .rx_data(w_uart_rx_core_rx_data),
        .rx_strobe(w_uart_rx_core_rx_strobe),
        .frame_err(w_uart_rx_core_frame_err)
    );

    rx_fifo #(.ADDR_BITS(2)) u_rx_fifo (
        .clk(clk),
        .rst(rst),
        .wr_en(w_uart_rx_core_rx_strobe),
        .wr_data(w_uart_rx_core_rx_data),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .overflow(w_rx_fifo_overflow)
    );

    rx_err_count u_rx_err_count (
        .clk(clk),
        .rst(rst),
        .ferr_in(w_uart_rx_core_frame_err),
        .ovf_in(w_rx_fifo_overflow),
        .ferr_count(ferr_count),
        .ovf_count(ovf_count)
    );

endmodule