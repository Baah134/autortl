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

    function integer clog2;
        input integer value;
        integer temp;
        begin
            temp = value - 1;
            clog2 = 0;
            while (temp > 0) begin
                clog2 = clog2 + 1;
                temp = temp >> 1;
            end
        end
    endfunction

    localparam PTR_WIDTH = (DEPTH <= 1) ? 1 : clog2(DEPTH);
    localparam COUNT_WIDTH = (DEPTH <= 1) ? 1 : clog2(DEPTH + 1);

    reg [WIDTH-1:0] data_mem [0:DEPTH-1];
    reg last_mem [0:DEPTH-1];

    reg [PTR_WIDTH-1:0] read_ptr;
    reg [PTR_WIDTH-1:0] write_ptr;
    reg [COUNT_WIDTH-1:0] occupancy;

    wire push;
    wire pop;
    wire [PTR_WIDTH-1:0] next_read_ptr;

    assign out_valid = (occupancy != 0);
    assign in_ready = (occupancy < DEPTH) || out_ready;
    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    assign next_read_ptr = (read_ptr == DEPTH - 1) ? {PTR_WIDTH{1'b0}} :
                           read_ptr + 1'b1;

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 0;
            write_ptr <= 0;
            occupancy <= 0;
            out_data <= 0;
            out_last <= 0;
        end else begin
            if (push) begin
                data_mem[write_ptr] <= in_data;
                last_mem[write_ptr] <= in_last;
                if (write_ptr == DEPTH - 1)
                    write_ptr <= 0;
                else
                    write_ptr <= write_ptr + 1'b1;
            end

            if (pop) begin
                read_ptr <= next_read_ptr;
                if (occupancy == 1) begin
                    if (push) begin
                        out_data <= in_data;
                        out_last <= in_last;
                    end
                end else begin
                    out_data <= data_mem[next_read_ptr];
                    out_last <= last_mem[next_read_ptr];
                end
            end else if (push && occupancy == 0) begin
                out_data <= in_data;
                out_last <= in_last;
            end

            case ({push, pop})
                2'b10: occupancy <= occupancy + 1'b1;
                2'b01: occupancy <= occupancy - 1'b1;
                default: occupancy <= occupancy;
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