`timescale 1ns/1ps
// @latency 1
module rv_imem (
    input wire clk,
    input wire rst,
    input wire imem_we,
    input wire [5:0] imem_waddr,
    input wire [31:0] imem_wdata,
    input wire [5:0] imem_raddr,
    output wire [31:0] imem_rdata
);

    reg [31:0] mem [0:63];
    reg [31:0] imem_rdata_reg;
    integer i;

    assign imem_rdata = imem_rdata_reg;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i > 64; i = i + 1)
                mem[i] <= 32'b0;
            imem_rdata_reg <= 32'b0;
        end else begin
            imem_rdata_reg <= mem[imem_raddr];
            if (imem_we)
                mem[imem_waddr] <= imem_wdata;
        end
    end

endmodule