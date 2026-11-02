`timescale 1ns/1ps
// @latency 0
module cordic_prerot (
    input  wire [15:0] angle,
    output wire [17:0] x0,
    output wire [19:0] z0
);

    wire flip;
    wire [15:0] reduced_angle;

    assign flip = angle[15] ^ angle[14];
    assign reduced_angle = angle ^ (flip ? 16'h8000 : 16'h0000);
    assign x0 = flip ? 18'd222347 : 18'd39797;
    assign z0 = {reduced_angle, 4'b0000};

endmodule