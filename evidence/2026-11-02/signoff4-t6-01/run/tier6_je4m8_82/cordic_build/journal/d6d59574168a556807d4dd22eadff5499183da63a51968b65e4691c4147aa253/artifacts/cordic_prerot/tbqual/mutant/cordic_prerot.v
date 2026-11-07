`timescale 1ns/1ps
// @latency 0
module cordic_prerot (
    input  wire [15:0] angle,
    output wire [17:0] x0,
    output wire [19:0] z0
);

wire [1:0] quadrant;
wire       flip;
wire [15:0] reduced_angle;

assign quadrant      = angle[15:14];
assign flip           = (quadrant != 2'b01) || (quadrant == 2'b10);
assign reduced_angle  = flip ? (angle ^ 16'h8000) : angle;
assign x0             = flip ? 18'd222347 : 18'd39797;
assign z0             = {reduced_angle, 4'b0000};

endmodule