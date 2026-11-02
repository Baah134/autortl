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
    reg [3:0] bit_index;
    reg [9:0] bit_phase;
    reg vote1;
    reg vote2;
    reg [7:0] rx_shift;
    reg [7:0] rx_data_reg;
    reg rx_strobe_reg;
    reg frame_err_reg;

    wire [10:0] next_phase = {1'b0, bit_phase} + 11'd1;
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
            bit_index     <= 4'd0;
            bit_phase     <= 10'd0;
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
                    bit_index <= 4'd0;
                    bit_phase <= 10'd0;
                    if (!sync2) begin
                        state     <= BUSY;
                        bit_index <= 4'd0;
                        bit_phase <= 10'd0;
                        rx_shift  <= 8'd0;
                    end
                end

                BUSY: begin
                    if (next_phase == (7 * OVERSAMPLE_DIV))
                        vote1 <= sync2;

                    if (next_phase == (8 * OVERSAMPLE_DIV))
                        vote2 <= sync2;

                    if (next_phase == (9 * OVERSAMPLE_DIV)) begin
                        if (bit_index == 4'd0) begin
                            if (majority_vote)
                                state <= IDLE;
                        end else if (bit_index <= 4'd8) begin
                            rx_shift <= {majority_vote, rx_shift[7:1]};
                        end else if (bit_index == 4'd9) begin
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

                    if (bit_phase == (BIT_TICKS - 1)) begin
                        bit_phase <= 10'd0;
                        bit_index <= bit_index + 1'b1;
                    end else begin
                        bit_phase <= bit_phase + 1'b1;
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

    localparam DEPTH = (1 << ADDR_BITS);

    reg [7:0] mem [0:DEPTH-1];
    reg [ADDR_BITS-1:0] rd_ptr;
    reg [ADDR_BITS-1:0] wr_ptr;
    reg [ADDR_BITS:0] count;
    reg [7:0] head_data_reg;
    reg out_valid_reg;
    reg overflow_reg;

    wire pop;
    wire push;
    wire [ADDR_BITS-1:0] next_rd_ptr = rd_ptr + 1'b1;

    assign out_valid = out_valid_reg;
    assign out_data = head_data_reg;
    assign overflow = overflow_reg;

    assign pop = out_ready && (count != 0);
    assign push = wr_en && ((count < DEPTH) || pop);

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr        <= {ADDR_BITS{1'b0}};
            wr_ptr        <= {ADDR_BITS{1'b0}};
            count         <= {(ADDR_BITS+1){1'b0}};
            head_data_reg <= 8'b0;
            out_valid_reg <= 1'b0;
            overflow_reg  <= 1'b0;
        end else begin
            overflow_reg <= wr_en && !push;

            if (pop)
                rd_ptr <= next_rd_ptr;

            if (push) begin
                mem[wr_ptr] <= wr_data;
                wr_ptr <= wr_ptr + 1'b1;
            end

            if (push && !pop) begin
                if (count == 0)
                    head_data_reg <= wr_data;
            end else if (pop) begin
                if (count == 1) begin
                    if (push)
                        head_data_reg <= wr_data;
                    else
                        head_data_reg <= 8'b0;
                end else begin
                    head_data_reg <= mem[next_rd_ptr];
                end
            end

            case ({push, pop})
                2'b10: begin
                    count <= count + 1'b1;
                    out_valid_reg <= 1'b1;
                end
                2'b01: begin
                    count <= count - 1'b1;
                    out_valid_reg <= (count != 1);
                end
                default: begin
                    count <= count;
                    out_valid_reg <= out_valid_reg;
                end
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