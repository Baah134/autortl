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
    reg [2:0] rd_ptr;
    reg [2:0] wr_ptr;
    reg [1:0] occupancy;

    wire push;
    wire pop;

    assign out_valid = (occupancy != 0);
    assign in_ready = (occupancy < 3) || out_ready;
    assign out_data = ({8{rd_ptr[0]}} & mem[0]) |
                      ({8{rd_ptr[1]}} & mem[1]) |
                      ({8{rd_ptr[2]}} & mem[2]);

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= 3'b001;
            wr_ptr <= 3'b001;
            occupancy <= 2'd0;
        end else begin
            if (push && wr_ptr[0])
                mem[0] <= in_data;
            if (push && wr_ptr[1])
                mem[1] <= in_data;
            if (push && wr_ptr[2])
                mem[2] <= in_data;

            if (push)
                wr_ptr <= {wr_ptr[1:0], wr_ptr[2]};

            if (pop)
                rd_ptr <= {rd_ptr[1:0], rd_ptr[2]};

            case ({push, pop})
                2'b10: occupancy <= occupancy + 1'b1;
                2'b01: occupancy <= occupancy - 1'b1;
                default: occupancy <= occupancy;
            endcase
        end
    end
endmodule