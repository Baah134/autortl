`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire [255:0] in,
    input  wire [7:0]   sel,
    output wire         out
);

    wire [31:0] group_out;
    wire [15:0] pair_out;
    wire [1:0]  upper_group_out;

    genvar g;
    generate
        for (g = 0; g < 32; g = g + 1) begin : gen_group
            wire [3:0] lower_inputs;
            wire [3:0] upper_inputs;
            wire lower_out;
            wire upper_out;

            assign lower_inputs = in[8*g +: 4];
            assign upper_inputs = in[8*g+4 +: 4];
            assign lower_out = lower_inputs[sel[1:0]];
            assign upper_out = upper_inputs[sel[1:0]];
            assign group_out[g] = sel[2] ? upper_out : lower_out;
        end
    endgenerate

    genvar p;
    generate
        for (p = 0; p < 16; p = p + 1) begin : gen_pair
            assign pair_out[p] = sel[3] ? group_out[2*p+1] : group_out[2*p];
        end
    endgenerate

    genvar u;
    generate
        for (u = 0; u < 2; u = u + 1) begin : gen_upper_group
            wire [3:0] lower_inputs;
            wire [3:0] upper_inputs;
            wire lower_out;
            wire upper_out;

            assign lower_inputs = pair_out[8*u +: 4];
            assign upper_inputs = pair_out[8*u+4 +: 4];
            assign lower_out = lower_inputs[sel[5:4]];
            assign upper_out = upper_inputs[sel[5:4]];
            assign upper_group_out[u] = sel[6] ? upper_out : lower_out;
        end
    endgenerate

    assign out = sel[7] ? upper_group_out[1] : upper_group_out[0];

endmodule