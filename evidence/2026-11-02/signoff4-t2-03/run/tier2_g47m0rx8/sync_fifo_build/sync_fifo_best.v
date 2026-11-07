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

    function integer clog2;
        input integer value;
        integer temp;
        begin
            temp = value - 1;
            clog2 = 0;
            while (temp > 0) begin
                temp = temp >> 1;
                clog2 = clog2 + 1;
            end
        end
    endfunction

    localparam PTR_WIDTH = (DEPTH <= 1) ? 1 : clog2(DEPTH);

    reg [WIDTH-1:0] mem [0:DEPTH-1];
    reg [PTR_WIDTH-1:0] rd_ptr;
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [DEPTH:0] occupancy_state;
    reg [WIDTH-1:0] out_data_reg;

    wire push;
    wire pop;
    wire not_full;
    wire [PTR_WIDTH-1:0] next_rd_ptr;

    assign out_valid = |occupancy_state[DEPTH:1];
    assign not_full = ~occupancy_state[DEPTH];
    assign in_ready = not_full || out_ready;
    assign out_data = out_data_reg;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    assign next_rd_ptr =
        (rd_ptr == DEPTH - 1) ? {PTR_WIDTH{1'b0}} : rd_ptr + 1'b1;

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= 0;
            wr_ptr <= 0;
            occupancy_state <= {{DEPTH{1'b0}}, 1'b1};
            out_data_reg <= 0;
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                if (wr_ptr == DEPTH - 1)
                    wr_ptr <= 0;
                else
                    wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop) begin
                rd_ptr <= next_rd_ptr;
            end

            case ({push, pop})
                2'b10: occupancy_state <= occupancy_state << 1;
                2'b01: occupancy_state <= occupancy_state >> 1;
                default: occupancy_state <= occupancy_state;
            endcase

            if (push && !pop && !out_valid)
                out_data_reg <= in_data;
            else if (pop && occupancy_state[1]) begin
                if (push)
                    out_data_reg <= in_data;
            end else if (pop)
                out_data_reg <= mem[next_rd_ptr];
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
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