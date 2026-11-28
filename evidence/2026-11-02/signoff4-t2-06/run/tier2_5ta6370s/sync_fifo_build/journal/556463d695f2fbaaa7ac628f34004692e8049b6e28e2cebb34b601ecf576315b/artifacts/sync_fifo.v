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
            clog2 = (i < 1) ? 1 : i;
        end
    endfunction

    localparam PTR_WIDTH = clog2(DEPTH);
    localparam COUNT_WIDTH = clog2(DEPTH + 1);

    reg [WIDTH-1:0] mem [0:DEPTH-1];
    reg [WIDTH-1:0] head_data;
    reg [PTR_WIDTH-1:0] rd_ptr;
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [COUNT_WIDTH-1:0] occupancy;
    reg nonempty;

    wire push;
    wire pop;
    wire [PTR_WIDTH-1:0] next_rd_ptr;

    assign out_valid = nonempty;
    assign in_ready = (occupancy < DEPTH) || out_ready;
    assign out_data = head_data;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;
    assign next_rd_ptr = (rd_ptr == DEPTH - 1) ?
                         {PTR_WIDTH{1'b0}} : rd_ptr + 1'b1;

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= {PTR_WIDTH{1'b0}};
            wr_ptr <= {PTR_WIDTH{1'b0}};
            occupancy <= {COUNT_WIDTH{1'b0}};
            head_data <= {WIDTH{1'b0}};
            nonempty <= 1'b0;
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                if (wr_ptr == DEPTH - 1)
                    wr_ptr <= {PTR_WIDTH{1'b0}};
                else
                    wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop) begin
                rd_ptr <= next_rd_ptr;
                if (occupancy == 1) begin
                    if (push)
                        head_data <= in_data;
                end else begin
                    head_data <= mem[next_rd_ptr];
                end
            end else if (push && (occupancy == 0)) begin
                head_data <= in_data;
            end

            case ({push, pop})
                2'b10: begin
                    occupancy <= occupancy + 1'b1;
                    nonempty <= 1'b1;
                end
                2'b01: begin
                    occupancy <= occupancy - 1'b1;
                    nonempty <= (occupancy > 1);
                end
                default: begin
                    occupancy <= occupancy;
                    nonempty <= nonempty;
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