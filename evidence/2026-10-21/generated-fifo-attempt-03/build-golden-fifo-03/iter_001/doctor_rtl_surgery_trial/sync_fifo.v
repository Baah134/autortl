`timescale 1ns/1ps
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
    reg [7:0] mem [0:2];
    reg [1:0] wr_ptr;
    reg [2:0] rd_sel;
    reg [3:0] occupancy_oh;

    wire push;
    wire pop;

    assign out_valid = ~occupancy_oh[0];
    assign in_ready = ~occupancy_oh[3] || out_ready;
    assign out_data =
        ({8{rd_sel[0]}} & mem[0]) |
        ({8{rd_sel[1]}} & mem[1]) |
        ({8{rd_sel[2]}} & mem[2]);

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            rd_sel <= 3'b001;
            wr_ptr <= 0;
            occupancy_oh <= 4'b0001;
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                if (wr_ptr == 2)
                    wr_ptr <= 0;
                else
                    wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop)
                rd_sel <= {rd_sel[1:0], rd_sel[2]};

            case ({push, pop})
                2'b10: occupancy_oh <= {occupancy_oh[2:0], 1'b0};
                2'b01: occupancy_oh <= {1'b0, occupancy_oh[3:1]};
                default: occupancy_oh <= occupancy_oh;
            endcase
        end
    end
endmodule