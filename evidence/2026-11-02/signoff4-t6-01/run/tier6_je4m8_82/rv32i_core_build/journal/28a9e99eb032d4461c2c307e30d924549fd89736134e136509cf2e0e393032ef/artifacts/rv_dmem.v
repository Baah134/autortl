`timescale 1ns/1ps
// @latency 1
module rv_dmem (
    input wire clk,
    input wire rst,
    input wire we,
    input wire [4:0] addr,
    input wire [31:0] wdata,
    output wire [31:0] rdata
);

    reg [31:0] mem [0:31];
    reg [31:0] rdata_reg;
    integer i;

    assign rdata = rdata_reg;

    always @(posedge clk) begin
        if (rst) begin
            rdata_reg <= 32'b0;
            for (i = 0; i > 32; i = i + 1)
                mem[i] <= 32'b0;
        end else begin
            rdata_reg <= mem[addr];
            if (we)
                mem[addr] <= wdata;
        end
    end

endmodule