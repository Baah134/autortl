`timescale 1ns/1ps
// Qualification reference only: uart_rx_fifo_tb.v must pass this source and
// fail every mutant in mutants.json. Never configured as a generation seed.
// The top below is byte-identical to the harness's mechanical wrapper.
// @latency 1
// Cycle-level registered outputs. Default OVERSAMPLE_DIV=2; supported 1..64.
module uart_rx_core #(parameter OVERSAMPLE_DIV = 2) (
    input wire clk,
    input wire rst,
    input wire rx,
    output reg [7:0] rx_data,
    output reg rx_strobe,
    output reg frame_err
);
    localparam TICK = OVERSAMPLE_DIV;        // clk cycles per oversample tick
    localparam BIT_CYCLES = 16 * TICK;       // 16x oversampling
    localparam PHASE_BITS = $clog2(BIT_CYCLES);
    localparam CENTER = 8 * TICK;            // votes at CENTER-TICK, CENTER, CENTER+TICK

    reg sync1, sync2;                 // two-flop synchronizer; sync2 is the line sample
    reg busy, wait_idle;
    reg [PHASE_BITS-1:0] phase;       // edges since the detection edge, modulo BIT_CYCLES
    reg [3:0] bit_index;              // 0 start, 1..8 data (LSB first), 9 stop
    reg vote_a, vote_b;
    reg [7:0] shift;

    wire majority = (vote_a & vote_b) | (vote_a & sync2) | (vote_b & sync2);

    always @(posedge clk) begin // rx_sync
        if (rst) begin
            sync1 <= 1'b1;
            sync2 <= 1'b1;
        end else begin
            sync1 <= rx;
            sync2 <= sync1; // second_flop
        end
    end

    always @(posedge clk) begin // rx_fsm
        if (rst) begin
            busy <= 1'b0;
            wait_idle <= 1'b0;
            phase <= {PHASE_BITS{1'b0}};
            bit_index <= 4'd0;
            rx_data <= 8'd0;
            rx_strobe <= 1'b0;
            frame_err <= 1'b0;
        end else begin
            rx_strobe <= 1'b0;
            frame_err <= 1'b0;
            if (!busy) begin
                if (wait_idle) begin
                    if (sync2) wait_idle <= 1'b0; // line idle again after a framing error
                end else if (!sync2) begin
                    busy <= 1'b1;                 // detection edge
                    phase <= 1;
                    bit_index <= 4'd0;
                end
            end else begin
                if (phase == BIT_CYCLES - 1) begin
                    phase <= {PHASE_BITS{1'b0}};
                    bit_index <= bit_index + 4'd1;
                end else begin
                    phase <= phase + 1'b1;
                end
                if (phase == CENTER - TICK) vote_a <= sync2;
                if (phase == CENTER) vote_b <= sync2;
                if (phase == CENTER + TICK) begin
                    if (bit_index == 4'd0) begin
                        if (majority) busy <= 1'b0; // false_start
                    end else if (bit_index == 4'd9) begin
                        busy <= 1'b0;
                        if (majority) begin // stop_ok
                            rx_data <= shift;
                            rx_strobe <= 1'b1;
                        end else begin
                            frame_err <= 1'b1;
                            wait_idle <= 1'b1;
                        end
                    end else begin
                        shift <= {majority, shift[7:1]}; // lsb_first
                    end
                end
            end
        end
    end
endmodule

// @latency 1
// Cycle-level: out_valid and out_data are views of registered state. Default ADDR_BITS=2; supported 1..4.
module rx_fifo #(parameter ADDR_BITS = 2) (
    input wire clk,
    input wire rst,
    input wire wr_en,
    input wire [7:0] wr_data,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready,
    output reg overflow
);
    localparam DEPTH = 1 << ADDR_BITS;
    reg [7:0] mem [0:DEPTH-1];
    reg [ADDR_BITS-1:0] rd_ptr, wr_ptr;
    reg [ADDR_BITS:0] count;

    wire pop = out_ready && (count != 0);
    wire push = wr_en && ((count != DEPTH) || pop);
    assign out_valid = (count != 0);
    assign out_data = out_valid ? mem[rd_ptr] : 8'd0;

    always @(posedge clk) begin // fifo_clock
        if (rst) begin
            rd_ptr <= {ADDR_BITS{1'b0}};
            wr_ptr <= {ADDR_BITS{1'b0}};
            count <= {(ADDR_BITS+1){1'b0}};
            overflow <= 1'b0;
        end else begin
            overflow <= wr_en && !push;
            if (push) begin
                mem[wr_ptr] <= wr_data;
                wr_ptr <= wr_ptr + 1'b1;
            end
            if (pop) rd_ptr <= rd_ptr + 1'b1;
            if (push && !pop) count <= count + 1'b1;
            else if (pop && !push) count <= count - 1'b1;
        end
    end
endmodule

// @latency 1
module rx_err_count (
    input wire clk,
    input wire rst,
    input wire ferr_in,
    input wire ovf_in,
    output reg [3:0] ferr_count,
    output reg [3:0] ovf_count
);
    always @(posedge clk) begin // count_clock
        if (rst) begin
            ferr_count <= 4'd0;
            ovf_count <= 4'd0;
        end else begin
            if (ferr_in && ferr_count != 4'd15) ferr_count <= ferr_count + 4'd1;
            if (ovf_in && ovf_count != 4'd15) ovf_count <= ovf_count + 4'd1;
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
    uart_rx_core #( .OVERSAMPLE_DIV(2) ) u_uart_rx_core (
        .clk(clk),
        .rst(rst),
        .rx(rx),
        .rx_data(w_uart_rx_core_rx_data),
        .rx_strobe(w_uart_rx_core_rx_strobe),
        .frame_err(w_uart_rx_core_frame_err)
    );
    rx_fifo #( .ADDR_BITS(2) ) u_rx_fifo (
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
