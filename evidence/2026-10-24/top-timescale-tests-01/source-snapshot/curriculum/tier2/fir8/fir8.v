// Deliberately naive 8-tap FIR: single-cycle sum of 8 products.
// @latency 1
module fir8 (
    input  wire               clk,
    input  wire               rst,
    input  wire signed [15:0] x_in,
    output reg  signed [31:0] y_out
);
    parameter signed [15:0] C0=16'd3, C1=16'd7, C2=16'd12, C3=16'd18,
                            C4=16'd18, C5=16'd12, C6=16'd7,  C7=16'd3;
    reg signed [15:0] d [0:7];
    integer i;
    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1) d[i] <= 16'sd0;
            y_out <= 32'sd0;
        end else begin
            d[0] <= x_in;
            for (i = 1; i < 8; i = i + 1) d[i] <= d[i-1];
            y_out <= d[0]*C0 + d[1]*C1 + d[2]*C2 + d[3]*C3
                   + d[4]*C4 + d[5]*C5 + d[6]*C6 + d[7]*C7;
        end
    end
endmodule
