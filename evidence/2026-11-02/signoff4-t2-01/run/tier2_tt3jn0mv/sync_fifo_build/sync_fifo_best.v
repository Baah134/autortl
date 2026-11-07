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
            clog2 = i;
        end
    endfunction

    localparam COUNT_WIDTH = (DEPTH <= 1) ? 1 : clog2(DEPTH + 1);

    reg [WIDTH-1:0] queue [0:DEPTH-1];
    reg [COUNT_WIDTH-1:0] occupancy;

    wire push;
    wire pop;
    integer i;

    assign in_ready = (occupancy < DEPTH) || out_ready;
    assign out_data = queue[0];

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 0;
            out_valid <= 1'b0;
        end else begin
            if (pop) begin
                for (i = 0; i < DEPTH-1; i = i + 1)
                    queue[i] <= queue[i+1];
            end

            if (push)
                queue[occupancy - pop] <= in_data;

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