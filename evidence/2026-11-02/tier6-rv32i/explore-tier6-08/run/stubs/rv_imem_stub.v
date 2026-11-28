module rv_imem (
    input wire clk,
    input wire rst,
    input wire imem_we,
    input wire [5:0] imem_waddr,
    input wire [31:0] imem_wdata,
    input wire [5:0] imem_raddr,
    output wire [31:0] imem_rdata
);
endmodule
