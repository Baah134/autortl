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

    localparam COUNT_WIDTH = count_width(DEPTH);

    reg [WIDTH-1:0] data_mem [0:DEPTH-1];
    reg last_mem [0:DEPTH-1];

    integer read_ptr;
    integer write_ptr;
    reg [COUNT_WIDTH-1:0] occupancy;
    reg full;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = !full || out_ready;
    assign out_data = data_mem[read_ptr];
    assign out_last = last_mem[read_ptr];

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 0;
            write_ptr <= 0;
            occupancy <= 0;
            full <= 1'b0;
        end else begin
            if (push) begin
                data_mem[write_ptr] <= in_data;
                last_mem[write_ptr] <= in_last;
                if (write_ptr == DEPTH-1)
                    write_ptr <= 0;
                else
                    write_ptr <= write_ptr + 1;
            end

            if (pop) begin
                if (read_ptr == DEPTH-1)
                    read_ptr <= 0;
                else
                    read_ptr <= read_ptr + 1;
            end

            case ({push, pop})
                2'b10: begin
                    occupancy <= occupancy + 1'b1;
                    full <= (occupancy == DEPTH-1);
                end
                2'b01: begin
                    occupancy <= occupancy - 1'b1;
                    full <= 1'b0;
                end
                default: begin
                    occupancy <= occupancy;
                    full <= full;
                end
            endcase
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
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