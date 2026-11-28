`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire [255:0] in,
    input  wire [7:0]   sel,
    output wire         out
);

    (* keep = "true" *) wire [15:0] group_out;
    (* keep = "true" *) wire [3:0] quartet_out;

    genvar group_index;
    genvar quartet_index;
    generate
        for (group_index = 0; group_index < 16; group_index = group_index + 1) begin : gen_group
            wire [15:0] group_data;

            assign group_data = in[16*group_index +: 16];
            assign group_out[group_index] = group_data[sel[3:0]];
        end

        for (quartet_index = 0; quartet_index < 4; quartet_index = quartet_index + 1) begin : gen_quartet
            wire [3:0] quartet_data;

            assign quartet_data = group_out[4*quartet_index +: 4];
            assign quartet_out[quartet_index] = quartet_data[sel[5:4]];
        end
    endgenerate

    assign out = quartet_out[sel[7:6]];

endmodule