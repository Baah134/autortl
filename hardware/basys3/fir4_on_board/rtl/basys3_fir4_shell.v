`timescale 1ns / 1ps
`default_nettype none
// Hand-written Basys 3 shell around the harness-generated signed_fir4
// (dut/signed_fir4.v, byte-identical to the verified winner).
//
// Each byte from the PC is one signed 8-bit sample x. Each filter output
// (13-bit signed) returns as two bytes: the sign-extended 16-bit value,
// low byte first. A UART break from the PC restarts the filter and
// flushes both FIFOs, so every test run starts from reset.
//   led[7:0]  last sample received
//   LD14      latches when a break (filter restart) was received
//   LD15      latches if the input FIFO ever overflowed (a sample was lost)
// The PC must not have more than 2^IN_FIFO_LOG2 samples outstanding.
module basys3_fir4_shell #(
    parameter CLKS_PER_BIT  = 868,        // 100 MHz / 115200 baud
    parameter IN_FIFO_LOG2  = 5,
    parameter OUT_FIFO_LOG2 = 5
) (
    input  wire       clk,                // 100 MHz, pin W5
    input  wire       btnC,
    input  wire       RsRx,               // from PC
    output wire       RsTx,               // to PC
    output wire [7:0] led,
    output wire       led_break,
    output wire       led_overflow
);
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

    // A break restarts the datapath. The UART itself is not reset, so a
    // byte already being transmitted still completes.
    reg soft_rst = 1'b1;
    always @(posedge clk) soft_rst <= btn_rst | rx_break;
    wire rst = btn_rst | soft_rst;

    wire [7:0] in_dout;
    wire       in_empty, in_full;
    wire       dut_in_ready;
    wire       dut_in_valid = !in_empty;

    sync_fifo #(.WIDTH(8), .DEPTH_LOG2(IN_FIFO_LOG2)) u_in_fifo (
        .clk(clk), .rst(rst),
        .wr_en(rx_valid), .din(rx_data),
        .rd_en(dut_in_valid && dut_in_ready), .dout(in_dout),
        .empty(in_empty), .full(in_full)
    );

    wire signed [12:0] dut_out_data;
    wire               dut_out_valid;
    wire               out_full;

    signed_fir4 u_dut (
        .clk(clk), .rst(rst),
        .x(in_dout), .in_valid(dut_in_valid), .in_ready(dut_in_ready),
        .out_data(dut_out_data), .out_valid(dut_out_valid), .out_ready(!out_full)
    );

    // Serializer: each 16-bit word goes out low byte, then high byte.
    localparam S_IDLE = 2'd0, S_LOW = 2'd1, S_HIGH = 2'd2;
    reg  [1:0]  ser_state;
    reg  [15:0] word;
    wire [15:0] out_dout;
    wire        out_empty;
    wire        tx_busy;
    wire        ser_take = (ser_state == S_IDLE) && !out_empty;
    wire        tx_start = !tx_busy && (ser_state == S_LOW || ser_state == S_HIGH);
    wire [7:0]  tx_data  = (ser_state == S_LOW) ? word[7:0] : word[15:8];

    sync_fifo #(.WIDTH(16), .DEPTH_LOG2(OUT_FIFO_LOG2)) u_out_fifo (
        .clk(clk), .rst(rst),
        .wr_en(dut_out_valid), .din({{3{dut_out_data[12]}}, dut_out_data}),
        .rd_en(ser_take), .dout(out_dout),
        .empty(out_empty), .full(out_full)
    );

    always @(posedge clk) begin
        if (rst) begin
            ser_state <= S_IDLE;
            word      <= 16'd0;
        end else begin
            case (ser_state)
                S_IDLE: if (!out_empty) begin
                            word      <= out_dout;
                            ser_state <= S_LOW;
                        end
                S_LOW:  if (!tx_busy) ser_state <= S_HIGH;
                S_HIGH: if (!tx_busy) ser_state <= S_IDLE;
                default: ser_state <= S_IDLE;
            endcase
        end
    end

    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_tx (
        .clk(clk), .rst(btn_rst),
        .start(tx_start), .data(tx_data),
        .tx(RsTx), .busy(tx_busy)
    );

    reg [7:0] last_sample;
    reg       break_seen, overflow;
    always @(posedge clk) begin
        if (btn_rst) begin
            last_sample <= 8'd0;
            break_seen  <= 1'b0;
            overflow    <= 1'b0;
        end else begin
            if (rx_valid)            last_sample <= rx_data;
            if (rx_break)            break_seen  <= 1'b1;
            if (rx_valid && in_full) overflow    <= 1'b1;
        end
    end
    assign led          = last_sample;
    assign led_break    = break_seen;
    assign led_overflow = overflow;
endmodule
`default_nettype wire
