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
    reg [8:0] data_mem [0:2];
    reg [1:0] read_ptr;
    reg [1:0] write_ptr;
    reg [1:0] occupancy;
    reg full_reg;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = !full_reg || out_ready;
    assign {out_last, out_data} = data_mem[read_ptr];

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 2'd0;
            write_ptr <= 2'd0;
            occupancy <= 2'd0;
            full_reg <= 1'b0;
        end else begin
            if (push) begin
                data_mem[write_ptr] <= {in_last, in_data};
                if (write_ptr == 2'd2)
                    write_ptr <= 2'd0;
                else
                    write_ptr <= write_ptr + 2'd1;
            end

            if (pop) begin
                if (read_ptr == 2'd2)
                    read_ptr <= 2'd0;
                else
                    read_ptr <= read_ptr + 2'd1;
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