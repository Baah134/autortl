module elastic_dot4_core (
    input wire clk,
    input wire rst,
    input wire [7:0] a0,
    input wire [7:0] b0,
    input wire [7:0] a1,
    input wire [7:0] b1,
    input wire [7:0] a2,
    input wire [7:0] b2,
    input wire [7:0] a3,
    input wire [7:0] b3,
    input wire in_valid,
    output wire in_ready,
    output wire [17:0] out_data,
    output wire out_valid,
    input wire out_ready
);
endmodule
