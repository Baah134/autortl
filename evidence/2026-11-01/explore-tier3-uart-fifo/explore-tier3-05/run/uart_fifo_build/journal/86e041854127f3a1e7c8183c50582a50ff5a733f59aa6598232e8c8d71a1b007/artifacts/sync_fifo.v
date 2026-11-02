`timescale 1ns/1ps
// @latency 1
module sync_fifo #(
    parameter DEPTH = 16,
    parameter WIDTH = 8
) (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [7:0] out_data
);

    function integer clog2;
        input integer value;
        integer i;
        begin
            value = value - 1;
            for (i = 0; value > 0; i = i + 1)
                value = value >> 1;
            clog2 = (i < 1) ? 1 : i;
        end
    endfunction

    localparam PTR_WIDTH = clog2(DEPTH);
    localparam COUNT_WIDTH = clog2(DEPTH + 1);

    reg [WIDTH-1:0] mem [0:DEPTH-1];
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [PTR_WIDTH-1:0] rd_ptr;
    reg [COUNT_WIDTH-1:0] count;

    wire push;
    wire pop;

    assign in_ready = (count < DEPTH);
    assign out_valid = (count != 0);
    assign out_data = mem[rd_ptr];

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

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
                    wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop) begin
                if (rd_ptr == DEPTH - 1)
                    rd_ptr <= 0;
                else
                    rd_ptr <= rd_ptr + 1'b1;
            end

            case ({push, pop})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: count <= count;
            endcase
        end
    end

endmodule