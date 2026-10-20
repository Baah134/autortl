// Registered MAC example; verify actual DSP mapping in target reports.
module mac_dsp #(parameter AW=18, BW=18, PW=48) (
    input  wire                 clk,
    input  wire                 rst,
    input  wire signed [AW-1:0] a,
    input  wire signed [BW-1:0] b,
    output reg  signed [PW-1:0] acc
);
    reg signed [AW-1:0] a_r;
    reg signed [BW-1:0] b_r;
    reg signed [AW+BW-1:0] p;
    always @(posedge clk) begin
        if (rst) begin
            a_r <= 0; b_r <= 0; p <= 0; acc <= 0;
        end else begin
            a_r <= a;
            b_r <= b;
            p   <= a_r * b_r;
            acc <= acc + p;
        end
    end
endmodule
