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

    function integer clog2;
        input integer value;
        integer i;
        begin
            clog2 = 0;
            for (i = value - 1; i > 0; i = i >> 1)
                clog2 = clog2 + 1;
        end
    endfunction

    localparam COUNT_WIDTH = (DEPTH <= 1) ? 1 : clog2(DEPTH + 1);

    reg [WIDTH-1:0] tail_data [0:((DEPTH > 1) ? DEPTH-2 : 0)];
    reg tail_last [0:((DEPTH > 1) ? DEPTH-2 : 0)];
    reg [COUNT_WIDTH-1:0] occupancy;
    reg [WIDTH-1:0] head_data;
    reg head_last;
    integer i;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = (occupancy < DEPTH) || out_ready;
    assign out_data = head_data;
    assign out_last = head_last;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 0;
            head_data <= 0;
            head_last <= 0;
        end else begin
            if (push && !pop) begin
                if (occupancy == 0) begin
                    head_data <= in_data;
                    head_last <= in_last;
                end else begin
                    for (i = 0; i < DEPTH-1; i = i + 1) begin
                        if (occupancy == i + 1) begin
                            tail_data[i] <= in_data;
                            tail_last[i] <= in_last;
                        end
                    end
                end
            end

            if (pop) begin
                if (occupancy == 1) begin
                    if (push) begin
                        head_data <= in_data;
                        head_last <= in_last;
                    end
                end else begin
                    head_data <= tail_data[0];
                    head_last <= tail_last[0];

                    for (i = 0; i < DEPTH-2; i = i + 1) begin
                        tail_data[i] <= tail_data[i+1];
                        tail_last[i] <= tail_last[i+1];
                    end

                    if (push) begin
                        for (i = 0; i < DEPTH-1; i = i + 1) begin
                            if (occupancy == i + 2) begin
                                tail_data[i] <= in_data;
                                tail_last[i] <= in_last;
                            end
                        end
                    end
                end
            end

            case ({push, pop})
                2'b10: occupancy <= occupancy + 1'b1;
                2'b01: occupancy <= occupancy - 1'b1;
                default: occupancy <= occupancy;
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