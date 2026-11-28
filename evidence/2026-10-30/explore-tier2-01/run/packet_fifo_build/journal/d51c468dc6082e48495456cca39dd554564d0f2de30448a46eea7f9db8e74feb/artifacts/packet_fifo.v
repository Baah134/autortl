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
    wire [7:0] core_out_data;
    wire core_out_last;
    wire push;
    wire pop;

    reg [8:0] output_queue [0:2];
    reg [1:0] queue_count;
    integer i;

    packet_fifo_core #(.WIDTH(8), .DEPTH(3)) u_packet_fifo_core (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_last(in_last),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(core_out_data),
        .out_last(core_out_last),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );

    assign out_data = output_queue[0][8:1];
    assign out_last = output_queue[0][0];
    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            queue_count <= 0;
        end else begin
            if (pop) begin
                for (i = 0; i < 2; i = i + 1)
                    output_queue[i] <= output_queue[i + 1];
            end

            if (push) begin
                if (pop) begin
                    case (queue_count)
                        2'd1: output_queue[0] <= {in_data, in_last};
                        2'd2: output_queue[1] <= {in_data, in_last};
                        default: output_queue[2] <= {in_data, in_last};
                    endcase
                end else begin
                    case (queue_count)
                        2'd0: output_queue[0] <= {in_data, in_last};
                        2'd1: output_queue[1] <= {in_data, in_last};
                        default: output_queue[2] <= {in_data, in_last};
                    endcase
                end
            end

            case ({push, pop})
                2'b10: queue_count <= queue_count + 1'b1;
                2'b01: queue_count <= queue_count - 1'b1;
                default: queue_count <= queue_count;
            endcase
        end
    end
endmodule