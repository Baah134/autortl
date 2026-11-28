`timescale 1ns/1ps
// @latency 1
module skid_buffer_core (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output reg out_valid,
    input wire out_ready
);

    reg [7:0] data0;
    reg [7:0] data1;
    reg [1:0] occupancy;
    reg [1:0] occupancy_next;

    wire push;
    wire pop;

    assign in_ready = (occupancy < 2) || out_ready;
    assign out_data = data0;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(*) begin
        occupancy_next = occupancy;
        if (push && !pop)
            occupancy_next = occupancy + 2'd1;
        else if (!push && pop)
            occupancy_next = occupancy - 2'd1;
    end

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 2'd0;
            out_valid <= 1'b0;
        end else begin
            occupancy <= occupancy_next;
            out_valid <= (occupancy_next != 0);

            if (pop && occupancy == 2'd2)
                data0 <= data1;
            else if (push && occupancy == 2'd0)
                data0 <= in_data;
            else if (push && pop && occupancy == 2'd1)
                data0 <= in_data;

            if (push && occupancy == 2'd1 && !pop)
                data1 <= in_data;
            else if (push && pop && occupancy == 2'd2)
                data1 <= in_data;
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
module skid_buffer (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    skid_buffer_core u_skid_buffer_core (
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