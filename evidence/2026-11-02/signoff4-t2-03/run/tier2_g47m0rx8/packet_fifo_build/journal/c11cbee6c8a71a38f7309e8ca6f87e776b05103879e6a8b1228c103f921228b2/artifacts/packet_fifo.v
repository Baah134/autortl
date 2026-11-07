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

    localparam integer TAIL_DEPTH = (DEPTH > 1) ? (DEPTH - 1) : 1;

    reg [WIDTH-1:0] tail_data_mem [0:TAIL_DEPTH-1];
    reg tail_last_mem [0:TAIL_DEPTH-1];
    reg [WIDTH-1:0] head_data;
    reg head_last;
    reg [2:0] read_ptr;
    reg [2:0] write_ptr;
    reg [3:0] occupancy;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = (occupancy < DEPTH) || out_ready;
    assign out_data = head_data;
    assign out_last = head_last;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 3'd0;
            write_ptr <= 3'd0;
            occupancy <= 4'd0;
        end else begin
            if (occupancy == 0) begin
                if (push) begin
                    head_data <= in_data;
                    head_last <= in_last;
                end
            end else begin
                if (pop) begin
                    if (occupancy > 1) begin
                        head_data <= tail_data_mem[read_ptr];
                        head_last <= tail_last_mem[read_ptr];
                    end else if (push) begin
                        head_data <= in_data;
                        head_last <= in_last;
                    end
                end

                if (push && !(pop && (occupancy == 1))) begin
                    tail_data_mem[write_ptr] <= in_data;
                    tail_last_mem[write_ptr] <= in_last;
                    if (write_ptr == TAIL_DEPTH-1)
                        write_ptr <= 3'd0;
                    else
                        write_ptr <= write_ptr + 1'b1;
                end

                if (pop && (occupancy > 1)) begin
                    if (read_ptr == TAIL_DEPTH-1)
                        read_ptr <= 3'd0;
                    else
                        read_ptr <= read_ptr + 1'b1;
                end
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