module axil_rd_if (
    input wire clk,
    input wire rst,
    input wire arvalid,
    output wire arready,
    input wire [5:0] araddr,
    output wire rvalid,
    input wire rready,
    output wire [31:0] rdata,
    output wire [1:0] rresp,
    input wire [255:0] regs_flat
);
endmodule
