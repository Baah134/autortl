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
                    if (phase_count == (7 * OVERSAMPLE_DIV - 1))
                        vote_a <= line_sample;

                    if (phase_count == (8 * OVERSAMPLE_DIV - 1))
                        vote_b <= line_sample;

                    if (phase_count == (9 * OVERSAMPLE_DIV - 1)) begin
                        if (bit_index == 4'd0) begin
                            if ((vote_a & vote_b) |
                                (vote_a & line_sample) |
                                (vote_b & line_sample)) begin
                                state <= IDLE;
                            end
                        end else if (bit_index >= 4'd1 && bit_index <= 4'd8) begin
                            data_bits <= {
                                (vote_a & vote_b) |
                                (vote_a & line_sample) |
                                (vote_b & line_sample),
                                data_bits[7:1]
                            };
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

`timescale 1ns/1ps
// @latency 1
module rx_fifo #(
    parameter ADDR_BITS = 2
) (
    input wire clk,
    input wire rst,
    input wire wr_en,
    input wire [7:0] wr_data,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready,
    output wire overflow
);

    localparam integer DEPTH = (1 << ADDR_BITS);

    reg [7:0] mem [0:DEPTH-1];
    reg [ADDR_BITS-1:0] rd_ptr;
    reg [ADDR_BITS-1:0] wr_ptr;
    reg [ADDR_BITS:0] count;
    reg [7:0] head_data_reg;
    reg overflow_reg;

    wire pop;
    wire push;

    assign pop = out_ready && (count != 0);
    assign push = wr_en && ((count < DEPTH) || pop);

    assign out_valid = (count != 0);
    assign out_data = head_data_reg;
    assign overflow = overflow_reg;

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= {ADDR_BITS{1'b0}};
            wr_ptr <= {ADDR_BITS{1'b0}};
            count <= {(ADDR_BITS+1){1'b0}};
            head_data_reg <= 8'b0;
            overflow_reg <= 1'b0;
        end else begin
            overflow_reg <= wr_en && !push;

            if (pop)
                rd_ptr <= rd_ptr + 1'b1;

            if (push) begin
                mem[wr_ptr] <= wr_data;
                wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop) begin
                if (count > 1)
                    head_data_reg <= mem[rd_ptr + 1'b1];
                else if (push)
                    head_data_reg <= wr_data;
                else
                    head_data_reg <= 8'b0;
            end else if (push && (count == 0)) begin
                head_data_reg <= wr_data;
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
                ferr_count_reg <= ferr_count_reg + 1'b1;

            if (ovf_in && (ovf_count_reg < 4'd15))
                ovf_count_reg <= ovf_count_reg + 1'b1;
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

    uart_rx_core #(
        .OVERSAMPLE_DIV(2)
    ) u_uart_rx_core (
        .clk(clk),
        .rst(rst),
        .rx(rx),
        .rx_data(w_uart_rx_core_rx_data),
        .rx_strobe(w_uart_rx_core_rx_strobe),
        .frame_err(w_uart_rx_core_frame_err)
    );

    rx_fifo #(
        .ADDR_BITS(2)
    ) u_rx_fifo (
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