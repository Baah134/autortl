`timescale 1ns/1ps
// @latency 1
module sync_byte_fifo #(
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

    reg [7:0] fifo [0:DEPTH-1];
    integer wr_ptr;
    integer rd_ptr;
    integer count;

    wire enqueue;
    wire dequeue;

    assign in_ready = (count < DEPTH);
    assign out_valid = (count != 0);
    assign out_data = out_valid ? fifo[rd_ptr] : 8'b0;

    assign enqueue = in_valid && in_ready && !rst;
    assign dequeue = out_valid && out_ready && !rst;

    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            count <= 0;
        end else begin
            if (enqueue) begin
                fifo[wr_ptr] <= in_data;
                if (wr_ptr == DEPTH - 1)
                    wr_ptr <= 0;
                else
                    wr_ptr <= wr_ptr + 1;
            end

            if (dequeue) begin
                if (rd_ptr == DEPTH - 1)
                    rd_ptr <= 0;
                else
                    rd_ptr <= rd_ptr + 1;
            end

            case ({enqueue, dequeue})
                2'b10: count <= count + 1;
                2'b01: count <= count - 1;
                default: count <= count;
            endcase
        end
    end

endmodule