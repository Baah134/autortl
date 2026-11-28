`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire [255:0] in,
    input  wire [7:0]   sel,
    output wire         out
);

    function mux16;
        input [15:0] data;
        input [3:0] index;
        reg [3:0] data0, data1, data2, data3;
        reg [3:0] mux4;
        reg [1:0] mux8;
        begin
            data0 = data[3:0];
            data1 = data[7:4];
            data2 = data[11:8];
            data3 = data[15:12];

            mux4[0] = data0[index[1:0]];
            mux4[1] = data1[index[1:0]];
            mux4[2] = data2[index[1:0]];
            mux4[3] = data3[index[1:0]];

            mux8[0] = index[2] ? mux4[1] : mux4[0];
            mux8[1] = index[2] ? mux4[3] : mux4[2];
            mux16   = index[3] ? mux8[1] : mux8[0];
        end
    endfunction

    wire [15:0] group_out;
    genvar group_index;

    generate
        for (group_index = 0; group_index < 16; group_index = group_index + 1) begin : gen_group
            assign group_out[group_index] = mux16(in[16*group_index +: 16], sel[3:0]);
        end
    endgenerate

    assign out = mux16(group_out, sel[7:4]);

endmodule