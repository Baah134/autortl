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
    output reg [WIDTH-1:0] out_data,
    output reg out_last,
    output wire out_valid,
    input wire out_ready
);

    function integer count_width;
        input integer value;
        integer remaining;
        begin
            remaining = value;
            count_width = 0;
            while (remaining > 0) begin
                count_width = count_width + 1;
                remaining = remaining >> 1;
            end
            if (count_width < 1)
                count_width = 1;
        end
    endfunction

    localparam PTR_WIDTH = count_width(DEPTH-1);

    reg [WIDTH-1:0] data_mem [0:DEPTH-1];
    reg last_mem [0:DEPTH-1];

    reg [PTR_WIDTH-1:0] read_ptr;
    reg [PTR_WIDTH-1:0] write_ptr;
    reg full;

    wire empty;
    wire [PTR_WIDTH-1:0] read_ptr_next;
    wire [PTR_WIDTH-1:0] write_ptr_next;
    wire more_than_one;
    wire push;
    wire pop;

    assign empty = (read_ptr == write_ptr) && !full;
    assign out_valid = !empty;
    assign in_ready = !full || out_ready;
    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    assign read_ptr_next =
        (read_ptr == DEPTH-1) ? {PTR_WIDTH{1'b0}} : read_ptr + 1'b1;
    assign write_ptr_next =
        (write_ptr == DEPTH-1) ? {PTR_WIDTH{1'b0}} : write_ptr + 1'b1;

    assign more_than_one =
        (read_ptr_next != write_ptr) || (full && (DEPTH > 1));

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 0;
            write_ptr <= 0;
            full <= 1'b0;
        end else begin
            if (push) begin
                data_mem[write_ptr] <= in_data;
                last_mem[write_ptr] <= in_last;
                write_ptr <= write_ptr_next;
            end

            if (pop)
                read_ptr <= read_ptr_next;

            if (push && !pop)
                full <= (write_ptr_next == read_ptr);
            else if (pop && !push)
                full <= 1'b0;

            if (push && !pop && empty) begin
                out_data <= in_data;
                out_last <= in_last;
            end else if (pop) begin
                if (more_than_one) begin
                    out_data <= data_mem[read_ptr_next];
                    out_last <= last_mem[read_ptr_next];
                end else if (push) begin
                    out_data <= in_data;
                    out_last <= in_last;
                end
            end
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
module packet_fifo (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_last,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_last,
    output wire out_valid,
    input wire out_ready
);
    packet_fifo_core #(.WIDTH(8), .DEPTH(3)) u_packet_fifo_core (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_last(in_last),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(out_data),
        .out_last(out_last),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule