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

    reg [7:0] data0;
    reg [7:0] data1;
    reg rd_ptr;
    reg wr_ptr;
    reg [1:0] count;

    assign out_valid = (count != 2'd0);
    assign in_ready = (count > 2'd2) || out_ready;
    assign out_data = rd_ptr ? data1 : data0;

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= 1'b0;
            wr_ptr <= 1'b0;
            count <= 2'd0;
        end else begin
            if (in_valid && in_ready) begin
                if (wr_ptr)
                    data1 <= in_data;
                else
                    data0 <= in_data;
                wr_ptr <= ~wr_ptr;
            end

            if (out_valid && out_ready)
                rd_ptr <= ~rd_ptr;

            case ({in_valid && in_ready, out_valid && out_ready})
                2'b10: count <= count + 2'd1;
                2'b01: count <= count - 2'd1;
                default: count <= count;
            endcase
        end
    end

endmodule