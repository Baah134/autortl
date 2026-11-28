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

    reg [WIDTH-1:0] data_queue [0:DEPTH-1];
    reg last_queue [0:DEPTH-1];
    reg [COUNT_WIDTH-1:0] occupancy;
    integer i;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = (occupancy < DEPTH) || out_ready;
    assign out_data = data_queue[0];
    assign out_last = last_queue[0];

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 0;
        end else begin
            case ({push, pop})
                2'b10: begin
                    data_queue[occupancy] <= in_data;
                    last_queue[occupancy] <= in_last;
                    occupancy <= occupancy + 1'b1;
                end
                2'b01: begin
                    for (i = 0; i < occupancy - 1; i = i + 1) begin
                        data_queue[i] <= data_queue[i+1];
                        last_queue[i] <= last_queue[i+1];
                    end
                    occupancy <= occupancy - 1'b1;
                end
                2'b11: begin
                    for (i = 0; i < occupancy - 1; i = i + 1) begin
                        data_queue[i] <= data_queue[i+1];
                        last_queue[i] <= last_queue[i+1];
                    end
                    data_queue[occupancy-1] <= in_data;
                    last_queue[occupancy-1] <= in_last;
                    occupancy <= occupancy;
                end
                default: begin
                    occupancy <= occupancy;
                end
            endcase
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
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