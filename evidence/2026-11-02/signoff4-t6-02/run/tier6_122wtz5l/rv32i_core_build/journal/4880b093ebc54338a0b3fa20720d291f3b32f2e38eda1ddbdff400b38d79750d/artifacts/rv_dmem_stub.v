module rv_dmem (
    input wire clk,
    input wire rst,
    input wire we,
    input wire [4:0] addr,
    input wire [31:0] wdata,
    output wire [31:0] rdata
);
endmodule
