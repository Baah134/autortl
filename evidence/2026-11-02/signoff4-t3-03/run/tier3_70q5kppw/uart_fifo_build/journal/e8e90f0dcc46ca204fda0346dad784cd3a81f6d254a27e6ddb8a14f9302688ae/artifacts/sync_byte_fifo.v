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
    output wire [7:0] data_out,
    output wire valid_out,
    input wire out_ready
);

    function integer clog2;
        input integer value;
        integer i;
        begin
            value = value - 1;
            for (i = 0; value > 0; i = i + 1)
                value = value >> 1;
            clog2 = i;
        end
    endfunction

    localparam PTR_W = (DEPTH <= 1) ? 1 : clog2(DEPTH);
    localparam COUNT_W = (DEPTH <= 1) ? 1 : clog2(DEPTH + 1);

    reg [7:0] mem [0:DEPTH-1];
    reg [PTR_W-1:0] rd_ptr;
    reg [PTR_W-1:0] wr_ptr;
    reg [COUNT_W-1:0] count;

    wire push;
    wire pop;
    wire bypass;

    assign in_ready = !rst && (count < DEPTH);
    assign bypass = (count == 0) && in_valid && !rst;
    assign valid_out = !rst && ((count != 0) || in_valid);
    assign data_out = !valid_out ? 8'b0 :
                      ((count == 0) ? in_data : mem[rd_ptr]);

    assign push = in_valid && in_ready;
    assign pop = valid_out && out_ready && !rst;

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= {PTR_W{1'b0}};
            wr_ptr <= {PTR_W{1'b0}};
            count <= {COUNT_W{1'b0}};
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                if (wr_ptr == DEPTH - 1)
                    wr_ptr <= {PTR_W{1'b0}};
                else
                    wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop) begin
                if (rd_ptr == DEPTH - 1)
                    rd_ptr <= {PTR_W{1'b0}};
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