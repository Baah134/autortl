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
    output wire out_valid,
    input wire out_ready
);

    localparam PTR_W = (DEPTH <= 1) ? 1 : $clog2(DEPTH);
    localparam CNT_W = (DEPTH <= 1) ? 1 : $clog2(DEPTH + 1);

    generate
        if (DEPTH == 3) begin: depth_three
            reg [WIDTH-1:0] entry0;
            reg [WIDTH-1:0] entry1;
            reg [WIDTH-1:0] entry2;
            reg [CNT_W-1:0] occupancy;

            wire push;
            wire pop;

            assign out_valid = (occupancy != 0);
            assign in_ready = (occupancy < 3) || out_ready;
            assign out_data = entry0;
            assign push = in_valid && in_ready;
            assign pop = out_valid && out_ready;

            always @(posedge clk) begin
                if (rst) begin
                    occupancy <= {CNT_W{1'b0}};
                end else begin
                    if (pop) begin
                        entry0 <= entry1;
                        entry1 <= entry2;
                        if (push) begin
                            if (occupancy == 1) begin
                                entry0 <= in_data;
                            end else if (occupancy == 2) begin
                                entry1 <= in_data;
                            end else begin
                                entry2 <= in_data;
                            end
                        end
                    end else if (push) begin
                        if (occupancy == 0)
                            entry0 <= in_data;
                        else if (occupancy == 1)
                            entry1 <= in_data;
                        else
                            entry2 <= in_data;
                    end

                    case ({push, pop})
                        2'b10: occupancy <= occupancy + 1'b1;
                        2'b01: occupancy <= occupancy - 1'b1;
                        default: occupancy <= occupancy;
                    endcase
                end
            end
        end else begin: other_depths
            reg [WIDTH-1:0] mem [0:DEPTH-1];
            reg [PTR_W-1:0] wr_ptr;
            reg [PTR_W-1:0] rd_ptr;
            reg [CNT_W-1:0] occupancy;

            wire push;
            wire pop;

            assign out_valid = (occupancy != 0);
            assign in_ready = (occupancy < DEPTH) || out_ready;
            assign out_data = mem[rd_ptr];
            assign push = in_valid && in_ready;
            assign pop = out_valid && out_ready;

            always @(posedge clk) begin
                if (rst) begin
                    wr_ptr <= {PTR_W{1'b0}};
                    rd_ptr <= {PTR_W{1'b0}};
                    occupancy <= {CNT_W{1'b0}};
                end else begin
                    if (push) begin
                        mem[wr_ptr] <= in_data;
                        if (wr_ptr == DEPTH - 1)
                            wr_ptr <= {PTR_W{1'b0}};
                        else
                            wr_ptr <= wr_ptr + 1'b1;
                    end

                    if (pop) begin
                        if (rd_ptr == DEPTH - 1)
                            rd_ptr <= {PTR_W{1'b0}};
                        else
                            rd_ptr <= rd_ptr + 1'b1;
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