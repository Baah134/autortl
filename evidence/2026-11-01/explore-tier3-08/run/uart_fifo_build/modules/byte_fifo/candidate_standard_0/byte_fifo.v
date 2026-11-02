`timescale 1ns/1ps
// @latency 1
module byte_fifo #(
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
    integer read_ptr;
    integer write_ptr;
    integer occupancy;

    assign in_ready = (occupancy < DEPTH);
    assign out_valid = (occupancy > 0);
    assign out_data = (occupancy > 0) ? mem[read_ptr] : 8'b0;

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 0;
            write_ptr <= 0;
            occupancy <= 0;
        end else begin
            if (in_valid && in_ready) begin
                mem[write_ptr] <= in_data;
                if (write_ptr == DEPTH - 1)
                    write_ptr <= 0;
                else
                    write_ptr <= write_ptr + 1;
            end

            if (out_valid && out_ready) begin
                if (read_ptr == DEPTH - 1)
                    read_ptr <= 0;
                else
                    read_ptr <= read_ptr + 1;
            end

            if ((in_valid && in_ready) && !(out_valid && out_ready))
                occupancy <= occupancy + 1;
            else if (!(in_valid && in_ready) && (out_valid && out_ready))
                occupancy <= occupancy - 1;
        end
    end

endmodule