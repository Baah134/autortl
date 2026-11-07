module rx_err_count (
    input wire clk,
    input wire rst,
    input wire ferr_in,
    input wire ovf_in,
    output wire [3:0] ferr_count,
    output wire [3:0] ovf_count
);
endmodule
