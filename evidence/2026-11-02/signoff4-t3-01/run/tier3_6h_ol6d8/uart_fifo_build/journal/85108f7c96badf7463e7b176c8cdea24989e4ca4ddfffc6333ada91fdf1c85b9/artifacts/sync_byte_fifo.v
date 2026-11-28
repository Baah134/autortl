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
    wire store_push;

    assign out_valid = (count > 0) || in_valid;
    assign out_data = (count > 0) ? mem[rd_ptr] :
                      (in_valid ? in_data : 8'b0);
    assign pop = out_valid && out_ready;
    assign in_ready = (count < DEPTH) || ((count > 0) && pop);
    assign push = in_valid && in_ready;
    assign store_push = push && !((count == 0) && out_ready);

    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            count <= 0;
        end else begin
            if (store_push) begin
                mem[wr_ptr] <= in_data;
                if (wr_ptr == DEPTH - 1)
                    wr_ptr <= 0;
                else
                    wr_ptr <= wr_ptr + 1;
            end

            if ((count > 0) && pop) begin
                if (rd_ptr == DEPTH - 1)
                    rd_ptr <= 0;
                else
                    rd_ptr <= rd_ptr + 1;
            end

            case ({store_push, ((count > 0) && pop)})
                2'b10: count <= count + 1;
                2'b01: count <= count - 1;
                default: count <= count;
            endcase
        end
    end

endmodule