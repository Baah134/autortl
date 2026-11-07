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

    reg [WIDTH-1:0] queue [0:DEPTH-1];
    reg [DEPTH-1:0] occupied;
    reg [DEPTH-1:0] occupied_after_pop;
    reg [DEPTH-1:0] occupied_next;

    wire push;
    wire pop;

    integer insert_index;
    integer i;

    assign out_valid = occupied[0];
    assign in_ready = !occupied[DEPTH-1] || out_ready;
    assign out_data = queue[0];

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(*) begin
        occupied_after_pop = occupied;
        if (pop)
            occupied_after_pop = occupied >> 1;

        insert_index = DEPTH;
        for (i = 0; i < DEPTH; i = i + 1) begin
            if ((insert_index == DEPTH) && !occupied_after_pop[i])
                insert_index = i;
        end

        occupied_next = occupied_after_pop;
        if (push && (insert_index < DEPTH))
            occupied_next[insert_index] = 1'b1;
    end

    always @(posedge clk) begin
        if (rst) begin
            occupied <= {DEPTH{1'b0}};
        end else begin
            occupied <= occupied_next;

            if (pop) begin
                for (i = 0; i < DEPTH-1; i = i + 1)
                    queue[i] <= queue[i+1];
            end

            if (push && (insert_index < DEPTH))
                queue[insert_index] <= in_data;
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