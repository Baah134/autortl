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

    reg [WIDTH-1:0] head_data;
    reg head_last;
    reg [WIDTH-1:0] tail_data [0:DEPTH-1];
    reg tail_last [0:DEPTH-1];
    reg [COUNT_WIDTH-1:0] occupancy;
    reg not_full;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = not_full || out_ready;
    assign out_data = head_data;
    assign out_last = head_last;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 0;
            not_full <= 1'b1;
        end else begin
            if (pop) begin
                if (occupancy > 1) begin
                    head_data <= tail_data[0];
                    head_last <= tail_last[0];
                end else if (push) begin
                    head_data <= in_data;
                    head_last <= in_last;
                end
            end else if (push && (occupancy == 0)) begin
                head_data <= in_data;
                head_last <= in_last;
            end

            case ({push, pop})
                2'b10: begin
                    occupancy <= occupancy + 1'b1;
                    not_full <= ((occupancy + 1'b1) < DEPTH);
                end
                2'b01: begin
                    occupancy <= occupancy - 1'b1;
                    not_full <= ((occupancy - 1'b1) < DEPTH);
                end
                default: begin
                    occupancy <= occupancy;
                    not_full <= not_full;
                end
            endcase
        end
    end

    genvar slot;
    generate
        for (slot = 0; slot < DEPTH; slot = slot + 1) begin: tail_slots
            if (slot < DEPTH-1) begin: with_shift
                always @(posedge clk) begin
                    if (!rst) begin
                        if (pop && (occupancy > 1)) begin
                            if (push && (occupancy == slot + 2)) begin
                                tail_data[slot] <= in_data;
                                tail_last[slot] <= in_last;
                            end else if (occupancy > slot + 2) begin
                                tail_data[slot] <= tail_data[slot+1];
                                tail_last[slot] <= tail_last[slot+1];
                            end
                        end else if (!pop && push &&
                                     (occupancy == slot + 1)) begin
                            tail_data[slot] <= in_data;
                            tail_last[slot] <= in_last;
                        end
                    end
                end
            end else begin: without_shift
                always @(posedge clk) begin
                    if (!rst) begin
                        if (pop && (occupancy > 1)) begin
                            if (push && (occupancy == slot + 2)) begin
                                tail_data[slot] <= in_data;
                                tail_last[slot] <= in_last;
                            end
                        end else if (!pop && push &&
                                     (occupancy == slot + 1)) begin
                            tail_data[slot] <= in_data;
                            tail_last[slot] <= in_last;
                        end
                    end
                end
            end
        end
    endgenerate

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