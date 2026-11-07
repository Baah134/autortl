`timescale 1ns/1ps
// @latency 1
module skid_buffer_core (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);

    reg [7:0] head_data;
    reg [7:0] tail_data;
    reg [1:0] occupancy;

    wire push;
    wire pop;

    assign in_ready = ~occupancy[1] || out_ready;
    assign out_valid = (occupancy != 0);
    assign out_data = head_data;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 2'd0;
        end else begin
            case (occupancy)
                2'd0: begin
                    if (push)
                        head_data <= in_data;
                end

                2'd1: begin
                    if (push && pop)
                        head_data <= in_data;
                    else if (push)
                        tail_data <= in_data;
                end

                2'd2: begin
                    if (pop) begin
                        head_data <= tail_data;
                        if (push)
                            tail_data <= in_data;
                    end
                end

                default: begin
                end
            endcase

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