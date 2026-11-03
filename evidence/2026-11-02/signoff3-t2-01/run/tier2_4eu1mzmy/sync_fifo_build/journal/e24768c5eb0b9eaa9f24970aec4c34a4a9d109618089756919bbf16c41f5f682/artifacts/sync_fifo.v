`timescale 1ns/1ps
// @latency 1
module sync_fifo_core #(
    parameter WIDTH = 8,
    parameter DEPTH = 3
) (
    input wire clk,
    input wire rst,
    input wire [WIDTH-1:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [WIDTH-1:0] out_data,
    output reg out_valid,
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

    localparam TAIL_DEPTH = (DEPTH > 1) ? (DEPTH - 1) : 1;
    localparam PTR_WIDTH = clog2(TAIL_DEPTH);
    localparam COUNT_WIDTH = clog2(DEPTH + 1);

    reg [WIDTH-1:0] memory [0:TAIL_DEPTH-1];
    reg [WIDTH-1:0] head;
    reg [PTR_WIDTH-1:0] read_ptr;
    reg [PTR_WIDTH-1:0] write_ptr;
    reg [COUNT_WIDTH-1:0] occupancy;

    wire push;
    wire pop;

    assign in_ready = (occupancy < DEPTH) || out_ready;
    assign out_data = head;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 0;
            write_ptr <= 0;
            occupancy <= 0;
            out_valid <= 1'b0;
        end else begin
            if (push && (occupancy == 0))
                head <= in_data;
            else if (pop && (occupancy == 1) && push)
                head <= in_data;
            else if (pop && (occupancy > 1))
                head <= memory[read_ptr];

            if (DEPTH > 1) begin
                if (push && (occupancy != 0) &&
                    !((occupancy == 1) && pop)) begin
                    memory[write_ptr] <= in_data;
                    if (write_ptr == TAIL_DEPTH - 1)
                        write_ptr <= 0;
                    else
                        write_ptr <= write_ptr + 1'b1;
                end

                if (pop && (occupancy > 1)) begin
                    if (read_ptr == TAIL_DEPTH - 1)
                        read_ptr <= 0;
                    else
                        read_ptr <= read_ptr + 1'b1;
                end
            end

            case ({push, pop})
                2'b10: begin
                    occupancy <= occupancy + 1'b1;
                    out_valid <= 1'b1;
                end
                2'b01: begin
                    occupancy <= occupancy - 1'b1;
                    out_valid <= (occupancy != 1);
                end
                default: begin
                    occupancy <= occupancy;
                    out_valid <= out_valid;
                end
            endcase
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
module sync_fifo (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    sync_fifo_core #(.WIDTH(8), .DEPTH(3)) u_sync_fifo_core (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule