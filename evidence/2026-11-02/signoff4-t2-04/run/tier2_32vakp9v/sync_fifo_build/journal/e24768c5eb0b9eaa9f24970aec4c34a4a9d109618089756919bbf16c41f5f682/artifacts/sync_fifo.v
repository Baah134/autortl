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

    localparam COUNT_WIDTH = (DEPTH <= 1) ? 1 : clog2(DEPTH + 1);
    localparam TAIL_DEPTH = (DEPTH > 1) ? DEPTH - 1 : 1;
    localparam TAIL_PTR_WIDTH = (TAIL_DEPTH <= 1) ? 1 : clog2(TAIL_DEPTH);

    reg [WIDTH-1:0] head_data;
    reg [COUNT_WIDTH-1:0] occupancy;

    wire push;
    wire pop;

    assign in_ready = (occupancy < DEPTH) || out_ready;
    assign out_data = head_data;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    generate
        if (DEPTH <= 1) begin : depth_one
            always @(posedge clk) begin
                if (rst) begin
                    head_data <= {WIDTH{1'b0}};
                    occupancy <= 0;
                    out_valid <= 1'b0;
                end else begin
                    if (push)
                        head_data <= in_data;

                    case ({push, pop})
                        2'b10: begin
                            occupancy <= occupancy + 1'b1;
                            out_valid <= 1'b1;
                        end
                        2'b01: begin
                            occupancy <= occupancy - 1'b1;
                            out_valid <= (occupancy > 1);
                        end
                        default: begin
                            occupancy <= occupancy;
                            out_valid <= out_valid;
                        end
                    endcase
                end
            end
        end else begin : depth_many
            reg [WIDTH-1:0] tail_mem [0:DEPTH-2];
            reg [TAIL_PTR_WIDTH-1:0] tail_wr_ptr;
            reg [TAIL_PTR_WIDTH-1:0] tail_rd_ptr;

            always @(posedge clk) begin
                if (rst) begin
                    head_data <= {WIDTH{1'b0}};
                    occupancy <= 0;
                    tail_wr_ptr <= 0;
                    tail_rd_ptr <= 0;
                    out_valid <= 1'b0;
                end else begin
                    if (push && (occupancy == 0))
                        head_data <= in_data;
                    else if (pop && (occupancy > 1))
                        head_data <= tail_mem[tail_rd_ptr];
                    else if (pop && push && (occupancy == 1))
                        head_data <= in_data;

                    if (push && (occupancy > 0) &&
                        !(pop && (occupancy == 1))) begin
                        tail_mem[tail_wr_ptr] <= in_data;
                        if (tail_wr_ptr == TAIL_DEPTH - 1)
                            tail_wr_ptr <= 0;
                        else
                            tail_wr_ptr <= tail_wr_ptr + 1'b1;
                    end

                    if (pop && (occupancy > 1)) begin
                        if (tail_rd_ptr == TAIL_DEPTH - 1)
                            tail_rd_ptr <= 0;
                        else
                            tail_rd_ptr <= tail_rd_ptr + 1'b1;
                    end

                    case ({push, pop})
                        2'b10: begin
                            occupancy <= occupancy + 1'b1;
                            out_valid <= 1'b1;
                        end
                        2'b01: begin
                            occupancy <= occupancy - 1'b1;
                            out_valid <= (occupancy > 1);
                        end
                        default: begin
                            occupancy <= occupancy;
                            out_valid <= out_valid;
                        end
                    endcase
                end
            end
        end
    endgenerate

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