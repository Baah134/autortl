`timescale 1ns/1ps
// @latency 1
module packet_fifo_core #(
    parameter WIDTH = 8,
    parameter DEPTH = 3
) (
    input wire clk,
    input wire rst,
    input wire [WIDTH-1:0] in_data,
    input wire in_last,
    input wire in_valid,
    output wire in_ready,
    output wire [WIDTH-1:0] out_data,
    output wire out_last,
    output wire out_valid,
    input wire out_ready
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

    reg [WIDTH:0] mem [0:DEPTH-1];
    reg [PTR_WIDTH-1:0] read_ptr;
    reg [PTR_WIDTH-1:0] write_ptr;
    reg [COUNT_WIDTH-1:0] occupancy;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = (occupancy < DEPTH) || out_ready;
    assign out_data = mem[read_ptr][WIDTH:1];
    assign out_last = mem[read_ptr][0];

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 0;
            write_ptr <= 0;
            occupancy <= 0;
        end else begin
            if (push) begin
                mem[write_ptr] <= {in_data, in_last};
                if (write_ptr == DEPTH - 1)
                    write_ptr <= 0;
                else
                    write_ptr <= write_ptr + 1'b1;
            end

            if (pop) begin
                if (read_ptr == DEPTH - 1)
                    read_ptr <= 0;
                else
                    read_ptr <= read_ptr + 1'b1;
            end

            case ({push, pop})
                2'b10: occupancy <= occupancy + 1'b1;
                2'b01: occupancy <= occupancy - 1'b1;
                default: occupancy <= occupancy;
            endcase
        end
    end

endmodule