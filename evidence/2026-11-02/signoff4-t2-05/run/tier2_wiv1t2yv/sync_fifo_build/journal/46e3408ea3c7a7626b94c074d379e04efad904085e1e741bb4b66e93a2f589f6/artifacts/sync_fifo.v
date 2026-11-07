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
        integer i;
        begin
            value = value - 1;
            for (i = 0; value > 0; i = i + 1)
                value = value >> 1;
            clog2 = i;
        end
    endfunction

    localparam PTR_WIDTH = (DEPTH > 1) ? clog2(DEPTH) : 1;
    localparam COUNT_WIDTH = clog2(DEPTH + 1);

    reg [WIDTH-1:0] mem [0:DEPTH-1];
    reg [PTR_WIDTH-1:0] rd_ptr;
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [COUNT_WIDTH-1:0] occupancy;
    reg valid_reg;

    wire push;
    wire pop;

    assign out_valid = valid_reg;
    assign in_ready = (occupancy < DEPTH) || out_ready;
    assign out_data = mem[rd_ptr];

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= 0;
            wr_ptr <= 0;
            occupancy <= 0;
            valid_reg <= 0;
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                if (wr_ptr == DEPTH - 1)
                    wr_ptr <= 0;
                else
                    wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop) begin
                if (rd_ptr == DEPTH - 1)
                    rd_ptr <= 0;
                else
                    rd_ptr <= rd_ptr + 1'b1;
            end

            case ({push, pop})
                2'b10: begin
                    occupancy <= occupancy + 1'b1;
                    valid_reg <= 1'b1;
                end
                2'b01: begin
                    occupancy <= occupancy - 1'b1;
                    valid_reg <= (occupancy > 1);
                end
                2'b11: begin
                    occupancy <= occupancy;
                    valid_reg <= 1'b1;
                end
                default: begin
                    occupancy <= occupancy;
                    valid_reg <= valid_reg;
                end
            endcase
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