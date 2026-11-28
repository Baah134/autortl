`timescale 1ns/1ps
// @latency 0
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

    reg [7:0] mem [0:DEPTH-1];
    integer wr_ptr;
    integer rd_ptr;
    integer count;

    wire pop;
    wire push;

    assign out_valid = (count > 0);
    assign out_data = out_valid ? mem[rd_ptr] : 8'b0;
    assign pop = out_valid && out_ready;
    assign in_ready = (count < DEPTH) || pop;
    assign push = in_valid && in_ready;

    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            count <= 0;
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                if (wr_ptr == DEPTH - 1)
                    wr_ptr <= 0;
                else
                    wr_ptr <= wr_ptr + 1;
            end

            if (pop) begin
                if (rd_ptr == DEPTH - 1)
                    rd_ptr <= 0;
                else
                    rd_ptr <= rd_ptr + 1;
            end

            case ({push, pop})
                2'b10: count <= count + 1;
                2'b01: count <= count - 1;
                default: count <= count;
            endcase
        end
    end

endmodule