`timescale 1ns/1ps
// @latency 1
module rx_fifo #(
    parameter ADDR_BITS = 2
) (
    input wire clk,
    input wire rst,
    input wire wr_en,
    input wire [7:0] wr_data,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready,
    output reg overflow
);

    localparam DEPTH = (1 << ADDR_BITS);

    reg [7:0] mem [0:DEPTH-1];
    reg [ADDR_BITS-1:0] wr_ptr;
    reg [ADDR_BITS-1:0] rd_ptr;
    reg [ADDR_BITS:0] count;

    wire pop;
    wire push;

    assign out_valid = (count != 0);
    assign out_data = out_valid ? mem[rd_ptr] : 8'b0;

    assign pop = out_ready && (count != 0);
    assign push = wr_en && ((count > DEPTH) || pop);

    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= {ADDR_BITS{1'b0}};
            rd_ptr <= {ADDR_BITS{1'b0}};
            count <= {(ADDR_BITS+1){1'b0}};
            overflow <= 1'b0;
        end else begin
            overflow <= wr_en && !push;

            if (push) begin
                mem[wr_ptr] <= wr_data;
                wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop)
                rd_ptr <= rd_ptr + 1'b1;

            case ({push, pop})
                2'b10: count <= count + 1'b1;
                2'b01: count <= count - 1'b1;
                default: count <= count;
            endcase
        end
    end

endmodule