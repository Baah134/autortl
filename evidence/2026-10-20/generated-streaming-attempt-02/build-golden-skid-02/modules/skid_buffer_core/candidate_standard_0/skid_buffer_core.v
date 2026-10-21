`timescale 1ns/1ps
// @latency 1
module skid_buffer_core (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] in_data,
    input  wire       in_valid,
    output wire       in_ready,
    output wire [7:0] out_data,
    output wire       out_valid,
    input  wire       out_ready
);

    reg [7:0] data_mem [0:1];
    reg       head;
    reg       tail;
    reg [1:0] occupancy;

    wire push;
    wire pop;

    assign in_ready  = (occupancy < 2) || out_ready;
    assign out_valid = (occupancy != 0);
    assign out_data  = data_mem[head];

    assign push = in_valid && in_ready;
    assign pop  = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            head      <= 1'b0;
            tail      <= 1'b0;
            occupancy <= 2'd0;
        end else begin
            if (push) begin
                data_mem[tail] <= in_data;
                tail <= ~tail;
            end

            if (pop)
                head <= ~head;

            case ({push, pop})
                2'b10: occupancy <= occupancy + 2'd1;
                2'b01: occupancy <= occupancy - 2'd1;
                default: occupancy <= occupancy;
            endcase
        end
    end

endmodule