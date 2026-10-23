`timescale 1ns/1ps
// @latency 1
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
    reg [8:0] entry0;
    reg [8:0] entry1;
    reg [8:0] entry2;
    reg [1:0] occupancy;
    reg full_reg;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = !full_reg || out_ready;
    assign out_data = entry0[7:0];
    assign out_last = entry0[8];

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            occupancy <= 2'd0;
            full_reg <= 1'b0;
        end else begin
            if (pop) begin
                entry0 <= entry1;
                entry1 <= entry2;
            end

            if (push) begin
                if (pop) begin
                    case (occupancy)
                        2'd1: entry0 <= {in_last, in_data};
                        2'd2: entry1 <= {in_last, in_data};
                        2'd3: entry2 <= {in_last, in_data};
                        default: entry0 <= {in_last, in_data};
                    endcase
                end else begin
                    case (occupancy)
                        2'd0: entry0 <= {in_last, in_data};
                        2'd1: entry1 <= {in_last, in_data};
                        2'd2: entry2 <= {in_last, in_data};
                        default: entry2 <= {in_last, in_data};
                    endcase
                end
            end

            case ({push, pop})
                2'b10: begin
                    occupancy <= occupancy + 2'd1;
                    full_reg <= (occupancy == 2'd2);
                end
                2'b01: begin
                    occupancy <= occupancy - 2'd1;
                    full_reg <= 1'b0;
                end
                default: begin
                    occupancy <= occupancy;
                    full_reg <= full_reg;
                end
            endcase
        end
    end
endmodule