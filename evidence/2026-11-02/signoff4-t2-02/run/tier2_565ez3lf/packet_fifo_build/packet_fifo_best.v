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

    localparam integer COUNT_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH + 1);
    localparam integer TAIL_DEPTH = DEPTH - 1;
    localparam integer TAIL_PTR_WIDTH = (TAIL_DEPTH <= 1) ? 1 : $clog2(TAIL_DEPTH);

    reg [WIDTH-1:0] head_data;
    reg head_last;
    reg [COUNT_WIDTH-1:0] occupancy;
    reg space_available;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = space_available || out_ready;
    assign out_data = head_data;
    assign out_last = head_last;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            space_available <= 1'b1;
        end else begin
            case ({push, pop})
                2'b10: space_available <= (occupancy < DEPTH - 1);
                2'b01: space_available <= 1'b1;
                default: space_available <= space_available;
            endcase
        end
    end

    generate
        if (DEPTH == 1) begin: depth_one
            always @(posedge clk) begin
                if (rst) begin
                    occupancy <= 0;
                    head_data <= 0;
                    head_last <= 0;
                end else begin
                    if (push && (occupancy == 0)) begin
                        head_data <= in_data;
                        head_last <= in_last;
                    end else if (push && pop) begin
                        head_data <= in_data;
                        head_last <= in_last;
                    end

                    case ({push, pop})
                        2'b10: occupancy <= occupancy + 1'b1;
                        2'b01: occupancy <= occupancy - 1'b1;
                        default: occupancy <= occupancy;
                    endcase
                end
            end
        end else begin: depth_many
            reg [WIDTH-1:0] tail_data [0:TAIL_DEPTH-1];
            reg tail_last [0:TAIL_DEPTH-1];
            reg [TAIL_PTR_WIDTH-1:0] tail_read_ptr;
            reg [TAIL_PTR_WIDTH-1:0] tail_write_ptr;

            always @(posedge clk) begin
                if (rst) begin
                    occupancy <= 0;
                    head_data <= 0;
                    head_last <= 0;
                    tail_read_ptr <= 0;
                    tail_write_ptr <= 0;
                end else begin
                    if (push && (occupancy == 0)) begin
                        head_data <= in_data;
                        head_last <= in_last;
                    end else if (pop && (occupancy == 1) && push) begin
                        head_data <= in_data;
                        head_last <= in_last;
                    end else if (pop && (occupancy > 1)) begin
                        head_data <= tail_data[tail_read_ptr];
                        head_last <= tail_last[tail_read_ptr];
                    end

                    if (push && (occupancy > 1)) begin
                        tail_data[tail_write_ptr] <= in_data;
                        tail_last[tail_write_ptr] <= in_last;
                        if (tail_write_ptr == TAIL_DEPTH - 1)
                            tail_write_ptr <= 0;
                        else
                            tail_write_ptr <= tail_write_ptr + 1'b1;
                    end else if (push && (occupancy == 1) && !pop) begin
                        tail_data[tail_write_ptr] <= in_data;
                        tail_last[tail_write_ptr] <= in_last;
                        if (tail_write_ptr == TAIL_DEPTH - 1)
                            tail_write_ptr <= 0;
                        else
                            tail_write_ptr <= tail_write_ptr + 1'b1;
                    end

                    if (pop && (occupancy > 1)) begin
                        if (tail_read_ptr == TAIL_DEPTH - 1)
                            tail_read_ptr <= 0;
                        else
                            tail_read_ptr <= tail_read_ptr + 1'b1;
                    end

                    case ({push, pop})
                        2'b10: occupancy <= occupancy + 1'b1;
                        2'b01: occupancy <= occupancy - 1'b1;
                        default: occupancy <= occupancy;
                    endcase
                end
            end
        end
    endgenerate

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