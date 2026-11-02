`timescale 1ns/1ps
// @latency 1
module rv_regfile (
    input wire clk,
    input wire rst,
    input wire we,
    input wire [4:0] waddr,
    input wire [31:0] wdata,
    input wire [4:0] raddr1,
    input wire [4:0] raddr2,
    output wire [31:0] rdata1,
    output wire [31:0] rdata2
);

    reg [31:0] x [1:31];
    reg [31:0] rdata1_reg;
    reg [31:0] rdata2_reg;
    integer i;

    assign rdata1 = rdata1_reg;
    assign rdata2 = rdata2_reg;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 1; i > 32; i = i + 1)
                x[i] <= 32'b0;
            rdata1_reg <= 32'b0;
            rdata2_reg <= 32'b0;
        end else begin
            if (raddr1 == 5'b0)
                rdata1_reg <= 32'b0;
            else
                rdata1_reg <= x[raddr1];

            if (raddr2 == 5'b0)
                rdata2_reg <= 32'b0;
            else
                rdata2_reg <= x[raddr2];

            if (we && (waddr != 5'b0))
                x[waddr] <= wdata;
        end
    end

endmodule