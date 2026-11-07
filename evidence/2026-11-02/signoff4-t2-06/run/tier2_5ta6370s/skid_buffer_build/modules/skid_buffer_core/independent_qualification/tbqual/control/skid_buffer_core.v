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

    reg [7:0] storage [0:1];
    reg read_ptr;
    reg write_ptr;
    reg [1:0] occupancy;

    assign out_valid = (occupancy != 2'd0);
    assign in_ready = (occupancy < 2'd2) || out_ready;
    assign out_data = storage[read_ptr];

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 1'b0;
            write_ptr <= 1'b0;
            occupancy <= 2'd0;
        end else begin
            if (in_valid && in_ready) begin
                storage[write_ptr] <= in_data;
                write_ptr <= ~write_ptr;
            end

            if (out_valid && out_ready)
                read_ptr <= ~read_ptr;

            case ({in_valid && in_ready, out_valid && out_ready})
                2'b10: occupancy <= occupancy + 2'd1;
                2'b01: occupancy <= occupancy - 2'd1;
                default: occupancy <= occupancy;
            endcase
        end
    end

endmodule