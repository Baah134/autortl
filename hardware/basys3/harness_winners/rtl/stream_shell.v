`timescale 1ns / 1ps
`default_nettype none
// Generic Basys 3 test shell for one harness-generated valid/ready design.
//
// The PC sends each transaction as IN_BYTES bytes, least significant byte
// first. The shell assembles them into one word and passes it to
// `stream_dut` (a thin per-design adapter around the unedited harness
// winner). Each result word returns as OUT_BYTES bytes, least significant
// first. A UART break restarts the datapath, so every run starts from reset.
//
// Between the FIFOs and the DUT, an LFSR traffic shaper creates legal
// valid/ready stress that UART-paced traffic would never produce:
// random input bubbles (in_valid is only raised at random times, and once
// raised it is held until accepted), per-cycle random out_ready, and long
// random stall phases. A stall phase can outlast a whole chunk of UART
// traffic, so queued transactions then burst into a DUT that is still full,
// forcing simultaneous accept and retire at every occupancy.
// STALL_LOG2 sets the longest phase (2^STALL_LOG2 cycles, at most 26).
//
//   led[7:0]      count of completed result words (low byte)
//   led_break     latches when a break (restart) was received
//   led_overflow  latches if the input FIFO ever overflowed
// The PC must keep at most 2^FIFO_LOG2 transactions outstanding.
module stream_shell #(
    parameter IN_BYTES     = 1,
    parameter OUT_BYTES    = 1,
    parameter CLKS_PER_BIT = 868,         // 100 MHz / 115200 baud
    parameter FIFO_LOG2    = 5,
    parameter STALL_LOG2   = 18           // up to 2.6 ms, about 30 UART bytes
) (
    input  wire       clk,
    input  wire       btnC,
    input  wire       RsRx,
    output wire       RsTx,
    output wire [7:0] led,
    output wire       led_break,
    output wire       led_overflow
);
    localparam IN_W  = 8 * IN_BYTES;
    localparam OUT_W = 8 * OUT_BYTES;

    (* ASYNC_REG = "TRUE" *) reg btn_meta = 1'b1, btn_rst = 1'b1;
    always @(posedge clk) begin
        btn_meta <= btnC;
        btn_rst  <= btn_meta;
    end

    wire [7:0] rx_data;
    wire       rx_valid, rx_break;

    uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_rx (
        .clk(clk), .rst(btn_rst), .rx(RsRx),
        .data(rx_data), .valid(rx_valid), .frame_err(rx_break)
    );

    // A break restarts the datapath; the UART itself keeps running.
    reg soft_rst = 1'b1;
    always @(posedge clk) soft_rst <= btn_rst | rx_break;
    wire rst = btn_rst | soft_rst;

    // Assemble IN_BYTES bytes, least significant first, into one word: each
    // byte enters at the top of the word and earlier bytes move down.
    reg  [7:0]      in_count;
    wire            in_word_done = rx_valid && (in_count == IN_BYTES - 1);
    wire [IN_W-1:0] in_word;
    generate
        if (IN_BYTES == 1) begin : g_one_byte
            assign in_word = rx_data;
        end else begin : g_multi_byte
            reg [IN_W-9:0] earlier;                         // bytes already received
            assign in_word = {rx_data, earlier};
            always @(posedge clk) begin
                if (rst)           earlier <= {(IN_W-8){1'b0}};
                else if (rx_valid) earlier <= in_word[IN_W-1:8];
            end
        end
    endgenerate
    always @(posedge clk) begin
        if (rst)           in_count <= 8'd0;
        else if (rx_valid) in_count <= in_word_done ? 8'd0 : in_count + 8'd1;
    end

    wire [IN_W-1:0] q_in;
    wire            q_in_empty, q_in_full;
    wire            dut_in_valid, dut_in_ready;

    shell_fifo #(.WIDTH(IN_W), .DEPTH_LOG2(FIFO_LOG2)) u_in_fifo (
        .clk(clk), .rst(rst),
        .wr_en(in_word_done), .din(in_word),
        .rd_en(dut_in_valid && dut_in_ready), .dout(q_in),
        .empty(q_in_empty), .full(q_in_full)
    );

    // Traffic shaper (maximal-length x^32 + x^22 + x^2 + x + 1 LFSR).
    reg [31:0]           lfsr = 32'hACE1_2026;
    reg                  stall_phase;
    reg [STALL_LOG2-1:0] phase_left;
    reg                  in_hold;
    always @(posedge clk) lfsr <= {lfsr[30:0], lfsr[31] ^ lfsr[21] ^ lfsr[1] ^ lfsr[0]};
    always @(posedge clk) begin
        if (rst) begin
            stall_phase <= 1'b0;
            phase_left  <= {STALL_LOG2{1'b0}};
        end else if (phase_left == 0) begin
            stall_phase <= lfsr[0];                         // half the phases stall
            phase_left  <= lfsr[STALL_LOG2+5:6];
        end else begin
            phase_left <= phase_left - 1'b1;
        end
    end
    // Each control combines widely separated LFSR bits. Adjacent bits of a
    // shift-register LFSR are the same sequence one cycle apart, which would
    // tie out_ready to the next cycle's offer and hide whole classes of bugs.
    wire offer_now  = (lfsr[11] ^ lfsr[26]) | (lfsr[17] ^ lfsr[30]);   // 3 in 4 cycles
    wire ready_draw = lfsr[3] ^ lfsr[20];                              // 1 in 2 cycles
    assign dut_in_valid = !q_in_empty && (offer_now || in_hold);
    always @(posedge clk) begin
        if (rst) in_hold <= 1'b0;
        else     in_hold <= dut_in_valid && !dut_in_ready;  // hold until accepted
    end

    wire [OUT_W-1:0] dut_out_word;
    wire             dut_out_valid;
    wire             q_out_full;
    wire             dut_out_ready = !q_out_full && !stall_phase && ready_draw;

    stream_dut u_dut (
        .clk(clk), .rst(rst),
        .in_word(q_in), .in_valid(dut_in_valid), .in_ready(dut_in_ready),
        .out_word(dut_out_word), .out_valid(dut_out_valid), .out_ready(dut_out_ready)
    );

    // Serialize each result word, least significant byte first.
    reg  [OUT_W-1:0] ser_word;
    reg  [7:0]       ser_left;                              // bytes still to start
    wire [OUT_W-1:0] q_out;
    wire             q_out_empty;
    wire             tx_busy;
    wire             ser_take = (ser_left == 0) && !tx_busy && !q_out_empty;
    wire             tx_start = (ser_left != 0) && !tx_busy;

    shell_fifo #(.WIDTH(OUT_W), .DEPTH_LOG2(FIFO_LOG2)) u_out_fifo (
        .clk(clk), .rst(rst),
        .wr_en(dut_out_valid && dut_out_ready), .din(dut_out_word),
        .rd_en(ser_take), .dout(q_out),
        .empty(q_out_empty), .full(q_out_full)
    );

    always @(posedge clk) begin
        if (rst) begin
            ser_word <= {OUT_W{1'b0}};
            ser_left <= 8'd0;
        end else if (ser_take) begin
            ser_word <= q_out;
            ser_left <= OUT_BYTES;
        end else if (tx_start) begin
            ser_word <= ser_word >> 8;
            ser_left <= ser_left - 8'd1;
        end
    end

    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_tx (
        .clk(clk), .rst(btn_rst),
        .start(tx_start), .data(ser_word[7:0]),
        .tx(RsTx), .busy(tx_busy)
    );

    reg [7:0] words_done;
    reg       break_seen, overflow;
    always @(posedge clk) begin
        if (btn_rst) begin
            words_done <= 8'd0;
            break_seen <= 1'b0;
            overflow   <= 1'b0;
        end else begin
            if (dut_out_valid && dut_out_ready) words_done <= words_done + 8'd1;
            if (rx_break)                       break_seen <= 1'b1;
            if (in_word_done && q_in_full)      overflow   <= 1'b1;
        end
    end
    assign led          = words_done;
    assign led_break    = break_seen;
    assign led_overflow = overflow;
endmodule
`default_nettype wire
