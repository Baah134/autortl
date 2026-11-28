`timescale 1ns/1ps
// Qualification reference only: uart_fifo_tb.v must pass this source and fail
// every mutant in mutants.json. Never configured as a generation seed.
// Children follow reference_spec.json; the top below is byte-identical to
// top_verilog() of that typed decomposition.
module sync_fifo #(parameter DEPTH = 8) (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    localparam AW = (DEPTH <= 2) ? 1 : $clog2(DEPTH);
    reg [7:0] mem [0:DEPTH-1];
    reg [AW-1:0] wr_ptr;
    reg [AW-1:0] rd_ptr;
    reg [AW:0] count;           // waiting bytes, 0..DEPTH

    wire push = in_valid && in_ready;
    wire pop = out_valid && out_ready;
    assign in_ready = (count < DEPTH);
    assign out_valid = (count != 0);
    assign out_data = mem[rd_ptr];

    always @(posedge clk) begin // fifo_mem
        if (push) mem[wr_ptr] <= in_data;
    end

    always @(posedge clk) begin // fifo_ctrl
        if (rst) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            count <= 0; // reset_count
        end else begin
            if (push) wr_ptr <= (wr_ptr == DEPTH - 1) ? 0 : wr_ptr + 1'b1;
            if (pop) rd_ptr <= (rd_ptr == DEPTH - 1) ? 0 : rd_ptr + 1'b1;
            if (push && !pop) count <= count + 1'b1;
            else if (pop && !push) count <= count - 1'b1;
        end
    end
endmodule

`timescale 1ns/1ps
module uart_tx #(parameter CLKS_PER_BIT = 16) (
    input wire clk,
    input wire rst,
    input wire [7:0] tx_data,
    input wire tx_valid,
    output wire tx_ready,
    output reg tx
);
    localparam TW = (CLKS_PER_BIT <= 2) ? 1 : $clog2(CLKS_PER_BIT);
    reg busy;
    reg [TW-1:0] tick;          // clk cycles elapsed in the current bit
    reg [3:0] bit_idx;          // 0 start, 1..8 data, 9 stop
    reg [7:0] shift;            // data bits not yet sent, next in [0]

    wire bit_done = (tick == CLKS_PER_BIT - 1);
    wire last_cycle = busy && bit_done && (bit_idx == 4'd9);
    assign tx_ready = !busy || last_cycle;
    wire start = tx_valid && tx_ready;

    always @(posedge clk) begin // tx_fsm
        if (rst) begin
            busy <= 1'b0;
            tx <= 1'b1;
            tick <= 0;
            bit_idx <= 4'd0;
        end else if (start) begin
            busy <= 1'b1;
            tx <= 1'b0; // start bit
            shift <= tx_data;
            tick <= 0;
            bit_idx <= 4'd0;
        end else if (busy) begin
            if (bit_done) begin
                tick <= 0;
                bit_idx <= bit_idx + 4'd1;
                if (bit_idx == 4'd9) begin
                    busy <= 1'b0; // frame_end, line already idle high
                end else if (bit_idx == 4'd8) begin
                    tx <= 1'b1; // stop bit
                end else begin
                    tx <= shift[0]; shift <= {1'b0, shift[7:1]}; // next_data_bit
                end
            end else begin
                tick <= tick + 1'b1;
            end
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
    wire [7:0] w_sync_fifo_out_data;
    wire w_sync_fifo_out_valid;
    wire w_uart_tx_tx_ready;
    sync_fifo #( .DEPTH(8) ) u_sync_fifo (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(w_sync_fifo_out_data),
        .out_valid(w_sync_fifo_out_valid),
        .out_ready(w_uart_tx_tx_ready)
    );
    uart_tx #( .CLKS_PER_BIT(16) ) u_uart_tx (
        .clk(clk),
        .rst(rst),
        .tx_data(w_sync_fifo_out_data),
        .tx_valid(w_sync_fifo_out_valid),
        .tx_ready(w_uart_tx_tx_ready),
        .tx(tx)
    );
endmodule
