module rv_ctrl (
    input wire clk,
    input wire rst,
    input wire run,
    input wire [2:0] kind,
    input wire [2:0] funct3,
    input wire [4:0] rd,
    input wire [31:0] y,
    input wire eq,
    input wire lt,
    input wire ltu,
    input wire [31:0] rs2_val,
    input wire [31:0] dmem_rdata,
    output wire [31:0] pc,
    output wire [5:0] imem_raddr,
    output wire retire,
    output wire rf_we,
    output wire [4:0] rf_waddr,
    output wire [31:0] rf_wdata,
    output wire dmem_we,
    output wire [4:0] dmem_addr,
    output wire [31:0] dmem_wdata
);
endmodule
