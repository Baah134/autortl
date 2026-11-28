`timescale 1ns/1ps
// Placement limitation: the fixed axil_regs interface exposes 165 I/O ports,
// which exceeds the target device's available I/O resources. RTL cannot resolve
// this while preserving the exact interface. Replanning must change the target
// device or the external interface.
module axil_regs (
    input wire clk,
    input wire rst,
    input wire awvalid,
    output wire awready,
    input wire [5:0] awaddr,
    input wire wvalid,
    output wire wready,
    input wire [31:0] wdata,
    input wire [3:0] wstrb,
    output wire bvalid,
    input wire bready,
    output wire [1:0] bresp,
    input wire arvalid,
    output wire arready,
    input wire [5:0] araddr,
    output wire rvalid,
    input wire rready,
    output wire [31:0] rdata,
    output wire [1:0] rresp,
    input wire [7:0] irq_set,
    input wire [31:0] status_in,
    output wire [31:0] ctrl,
    output wire irq
);
    wire w_axil_wr_if_wr_en;
    wire [2:0] w_axil_wr_if_wr_idx;
    wire [31:0] w_axil_wr_if_wr_data;
    wire [3:0] w_axil_wr_if_wr_strb;
    wire [255:0] w_axil_regbank_regs_flat;

    axil_wr_if u_axil_wr_if (
        .clk(clk),
        .rst(rst),
        .awvalid(awvalid),
        .awready(awready),
        .awaddr(awaddr),
        .wvalid(wvalid),
        .wready(wready),
        .wdata(wdata),
        .wstrb(wstrb),
        .bvalid(bvalid),
        .bready(bready),
        .bresp(bresp),
        .wr_en(w_axil_wr_if_wr_en),
        .wr_idx(w_axil_wr_if_wr_idx),
        .wr_data(w_axil_wr_if_wr_data),
        .wr_strb(w_axil_wr_if_wr_strb)
    );

    axil_regbank u_axil_regbank (
        .clk(clk),
        .rst(rst),
        .wr_en(w_axil_wr_if_wr_en),
        .wr_idx(w_axil_wr_if_wr_idx),
        .wr_data(w_axil_wr_if_wr_data),
        .wr_strb(w_axil_wr_if_wr_strb),
        .irq_set(irq_set),
        .status_in(status_in),
        .regs_flat(w_axil_regbank_regs_flat),
        .ctrl(ctrl),
        .irq(irq)
    );

    axil_rd_if u_axil_rd_if (
        .clk(clk),
        .rst(rst),
        .arvalid(arvalid),
        .arready(arready),
        .araddr(araddr),
        .rvalid(rvalid),
        .rready(rready),
        .rdata(rdata),
        .rresp(rresp),
        .regs_flat(w_axil_regbank_regs_flat)
    );
endmodule