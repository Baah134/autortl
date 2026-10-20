`timescale 1ns/1ps
// Logical async FIFO skeleton; AW >= 2, DW >= 1, depth 2**AW.
// Coordinated reset in BOTH domains with traffic stopped is required.
// Independent domain reset recovery is unsupported. Flags are conservative
// because remote Gray pointers traverse two synchronizer registers.
// rd_data holds unless a read is accepted; unspecified before the first read.
// Simulation does not prove metastability safety or physical CDC constraints.
module async_fifo #(parameter DW=8, AW=4) (
    input  wire          wr_clk, wr_rst, wr_en,
    input  wire [DW-1:0] wr_data,
    output wire          full,
    input  wire          rd_clk, rd_rst, rd_en,
    output reg  [DW-1:0] rd_data,
    output wire          empty
);
    reg [DW-1:0] mem [0:(1<<AW)-1];
    reg [AW:0] wptr_bin, wptr_gray, rptr_bin, rptr_gray;
    (* ASYNC_REG="TRUE" *) reg [AW:0] rptr_gray_w1, rptr_gray_w2;
    (* ASYNC_REG="TRUE" *) reg [AW:0] wptr_gray_r1, wptr_gray_r2;

    wire [AW:0] wptr_bin_n  = wptr_bin + (wr_en && !full);
    wire [AW:0] wptr_gray_n = (wptr_bin_n >> 1) ^ wptr_bin_n;
    wire [AW:0] rptr_bin_n  = rptr_bin + (rd_en && !empty);
    wire [AW:0] rptr_gray_n = (rptr_bin_n >> 1) ^ rptr_bin_n;

    always @(posedge wr_clk) begin
        if (wr_rst) begin wptr_bin <= 0; wptr_gray <= 0; end
        else begin
            if (wr_en && !full) mem[wptr_bin[AW-1:0]] <= wr_data;
            wptr_bin <= wptr_bin_n; wptr_gray <= wptr_gray_n;
        end
    end
    always @(posedge wr_clk) begin
        if (wr_rst) {rptr_gray_w2, rptr_gray_w1} <= 0;
        else {rptr_gray_w2, rptr_gray_w1} <= {rptr_gray_w1, rptr_gray};
    end
    assign full = (wptr_gray != {~rptr_gray_w2[AW:AW-1], rptr_gray_w2[AW-2:0]});

    always @(posedge rd_clk) begin
        if (rd_rst) begin rptr_bin <= 0; rptr_gray <= 0; end
        else begin
            if (rd_en && !empty) rd_data <= mem[rptr_bin[AW-1:0]];
            rptr_bin <= rptr_bin_n; rptr_gray <= rptr_gray_n;
        end
    end
    always @(posedge rd_clk) begin
        if (rd_rst) {wptr_gray_r2, wptr_gray_r1} <= 0;
        else {wptr_gray_r2, wptr_gray_r1} <= {wptr_gray_r1, wptr_gray};
    end
    assign empty = (rptr_gray == wptr_gray_r2);
endmodule
