`timescale 1ns/1ps
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
    localparam [31:0] ID_VALUE = 32'h52544C35;

    wire wr_en;
    wire [2:0] wr_idx;
    wire [31:0] wr_data;
    wire [3:0] wr_strb;

    reg [31:0] ctrl_q;
    reg [31:0] scratch_q;
    reg [31:0] config_q;
    reg [31:0] status_q;
    reg [31:0] wcount_q;
    reg [7:0] mask_q;
    reg [7:0] pend_q;

    wire [7:0] w1c_clear =
        (wr_en && (wr_idx == 3'd4) && wr_strb[0]) ? wr_data[7:0] : 8'd0;

    wire [255:0] regs_flat = {
        wcount_q,
        ID_VALUE,
        status_q,
        {24'd0, pend_q},
        {24'd0, mask_q},
        config_q,
        scratch_q,
        ctrl_q
    };

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
        .wr_en(wr_en),
        .wr_idx(wr_idx),
        .wr_data(wr_data),
        .wr_strb(wr_strb)
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
        .regs_flat(regs_flat)
    );

    always @(posedge clk) begin
        if (rst) begin
            ctrl_q <= 32'd0;
            scratch_q <= 32'd0;
            config_q <= 32'h00000100;
            status_q <= 32'd0;
            wcount_q <= 32'd0;
            mask_q <= 8'd0;
            pend_q <= 8'd0;
        end else begin
            status_q <= status_in;
            pend_q <= (pend_q & ~w1c_clear) | irq_set;

            if (wr_en) begin
                wcount_q <= wcount_q + 32'd1;
            end

            if (wr_en && (wr_idx == 3'd0) && wr_strb[0])
                ctrl_q[7:0] <= wr_data[7:0];
            if (wr_en && (wr_idx == 3'd0) && wr_strb[1])
                ctrl_q[15:8] <= wr_data[15:8];
            if (wr_en && (wr_idx == 3'd0) && wr_strb[2])
                ctrl_q[23:16] <= wr_data[23:16];
            if (wr_en && (wr_idx == 3'd0) && wr_strb[3])
                ctrl_q[31:24] <= wr_data[31:24];

            if (wr_en && (wr_idx == 3'd1) && wr_strb[0])
                scratch_q[7:0] <= wr_data[7:0];
            if (wr_en && (wr_idx == 3'd1) && wr_strb[1])
                scratch_q[15:8] <= wr_data[15:8];
            if (wr_en && (wr_idx == 3'd1) && wr_strb[2])
                scratch_q[23:16] <= wr_data[23:16];
            if (wr_en && (wr_idx == 3'd1) && wr_strb[3])
                scratch_q[31:24] <= wr_data[31:24];

            if (wr_en && (wr_idx == 3'd2) && wr_strb[0])
                config_q[7:0] <= wr_data[7:0];
            if (wr_en && (wr_idx == 3'd2) && wr_strb[1])
                config_q[15:8] <= wr_data[15:8];
            if (wr_en && (wr_idx == 3'd2) && wr_strb[2])
                config_q[23:16] <= wr_data[23:16];
            if (wr_en && (wr_idx == 3'd2) && wr_strb[3])
                config_q[31:24] <= wr_data[31:24];

            if (wr_en && (wr_idx == 3'd3) && wr_strb[0])
                mask_q <= wr_data[7:0];
        end
    end

    assign ctrl = ctrl_q;
    assign irq = |(pend_q & mask_q);
endmodule