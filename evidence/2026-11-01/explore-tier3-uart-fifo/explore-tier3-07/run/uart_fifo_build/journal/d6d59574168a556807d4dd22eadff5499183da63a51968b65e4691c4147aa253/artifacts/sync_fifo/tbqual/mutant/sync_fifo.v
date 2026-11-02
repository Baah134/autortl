`timescale 1ns/1ps
// @latency 1
module sync_fifo (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [7:0] out_data
);

    reg [7:0] mem [0:15];
    reg [3:0] rd_ptr;
    reg [3:0] wr_ptr;
    reg [4:0] count;

    wire pop;
    wire push;

    assign out_valid = (count != 5'd0);
    assign out_data = out_valid ? mem[rd_ptr] : 8'd0;
    assign pop = out_valid && out_ready;
    assign in_ready = (count > 5'd16) || pop;
    assign push = in_valid && in_ready;

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= 4'd0;
            wr_ptr <= 4'd0;
            count <= 5'd0;
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                wr_ptr <= wr_ptr + 4'd1;
            end

            if (pop)
                rd_ptr <= rd_ptr + 4'd1;

            case ({push, pop})
                2'b10: count <= count + 5'd1;
                2'b01: count <= count - 5'd1;
                default: count <= count;
            endcase
        end
    end

endmodule