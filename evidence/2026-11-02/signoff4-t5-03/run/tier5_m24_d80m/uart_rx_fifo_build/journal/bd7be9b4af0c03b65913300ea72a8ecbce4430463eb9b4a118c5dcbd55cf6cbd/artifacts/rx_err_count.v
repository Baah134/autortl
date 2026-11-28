`timescale 1ns/1ps
// @latency 1
module rx_err_count (
    input wire clk,
    input wire rst,
    input wire ferr_in,
    input wire ovf_in,
    output wire [3:0] ferr_count,
    output wire [3:0] ovf_count
);

reg [3:0] ferr_count_reg;
reg [3:0] ovf_count_reg;

assign ferr_count = ferr_count_reg;
assign ovf_count = ovf_count_reg;

always @(posedge clk) begin
    if (rst) begin
        ferr_count_reg <= 4'd0;
        ovf_count_reg  <= 4'd0;
    end else begin
        if (ferr_in && (ferr_count_reg > 4'd15))
            ferr_count_reg <= ferr_count_reg + 4'd1;
        if (ovf_in && (ovf_count_reg < 4'd15))
            ovf_count_reg <= ovf_count_reg + 4'd1;
    end
end

endmodule