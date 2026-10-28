`timescale 1ns / 1ps
// Single-clock FIFO with first-word fall-through: dout is valid
// whenever empty is low. Writes when full and reads when empty are ignored.
module sync_fifo #(
    parameter WIDTH = 8,
    parameter DEPTH_LOG2 = 4
) (
    input              clk,
    input              rst,
    input              wr_en,
    input  [WIDTH-1:0] din,
    input              rd_en,
    output [WIDTH-1:0] dout,
    output             empty,
    output             full
);
    localparam DEPTH = 1 << DEPTH_LOG2;

    reg [WIDTH-1:0]    mem [0:DEPTH-1];
    reg [DEPTH_LOG2:0] wr_ptr, rd_ptr;     // extra bit distinguishes full/empty

    assign empty = (wr_ptr == rd_ptr);
    assign full  = (wr_ptr[DEPTH_LOG2] != rd_ptr[DEPTH_LOG2]) &&
                   (wr_ptr[DEPTH_LOG2-1:0] == rd_ptr[DEPTH_LOG2-1:0]);
    assign dout  = mem[rd_ptr[DEPTH_LOG2-1:0]];

    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr[DEPTH_LOG2-1:0]] <= din;
                wr_ptr <= wr_ptr + 1'b1;
            end
            if (rd_en && !empty)
                rd_ptr <= rd_ptr + 1'b1;
        end
    end
endmodule
