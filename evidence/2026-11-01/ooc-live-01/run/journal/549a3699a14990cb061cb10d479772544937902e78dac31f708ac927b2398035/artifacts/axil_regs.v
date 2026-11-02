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
    reg aw_full;
    reg w_full;
    reg [5:0] aw_addr_q;
    reg [31:0] w_data_q;
    reg [3:0] w_strb_q;
    reg bvalid_q;
    reg [1:0] bresp_q;

    reg [31:0] ctrl_q;
    reg [31:0] scratch_q;
    reg [31:0] config_q;
    reg [7:0] mask_q;
    reg [7:0] pend_q;
    reg [31:0] status_q;
    reg [31:0] wcount_q;

    reg rvalid_q;
    reg [31:0] rdata_q;
    reg [1:0] rresp_q;

    wire do_write = aw_full && w_full && !bvalid_q;
    wire wr_en = do_write && !aw_addr_q[5];
    wire [2:0] wr_idx = aw_addr_q[4:2];
    wire [7:0] w1c_clear =
        (wr_en && (wr_idx == 3'd4) && w_strb_q[0]) ?
        w_data_q[7:0] : 8'd0;

    wire [31:0] selected_read_data;
    wire [255:0] regs_flat;

    assign awready = !aw_full;
    assign wready = !w_full;
    assign bvalid = bvalid_q;
    assign bresp = bresp_q;

    assign arready = !rvalid_q;
    assign rvalid = rvalid_q;
    assign rdata = rdata_q;
    assign rresp = rresp_q;

    assign regs_flat = {
        wcount_q,
        32'h52544C35,
        status_q,
        {24'd0, pend_q},
        {24'd0, mask_q},
        config_q,
        scratch_q,
        ctrl_q
    };
    assign selected_read_data =
        regs_flat[araddr[4:2] * 32 +: 32];

    assign ctrl = ctrl_q;
    assign irq = |(pend_q & mask_q);

    always @(posedge clk) begin
        if (rst) begin
            aw_full <= 1'b0;
            w_full <= 1'b0;
            aw_addr_q <= 6'd0;
            w_data_q <= 32'd0;
            w_strb_q <= 4'd0;
            bvalid_q <= 1'b0;
            bresp_q <= 2'b00;
        end else begin
            if (do_write) begin
                aw_full <= 1'b0;
                w_full <= 1'b0;
                bvalid_q <= 1'b1;
                bresp_q <= aw_addr_q[5] ? 2'b10 : 2'b00;
            end else if (bvalid_q && bready) begin
                bvalid_q <= 1'b0;
            end

            if (awvalid && awready) begin
                aw_full <= 1'b1;
                aw_addr_q <= awaddr;
            end

            if (wvalid && wready) begin
                w_full <= 1'b1;
                w_data_q <= wdata;
                w_strb_q <= wstrb;
            end
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            ctrl_q <= 32'd0;
            scratch_q <= 32'd0;
            config_q <= 32'h00000100;
            mask_q <= 8'd0;
            pend_q <= 8'd0;
            status_q <= 32'd0;
            wcount_q <= 32'd0;
        end else begin
            status_q <= status_in;
            pend_q <= (pend_q & ~w1c_clear) | irq_set;

            if (wr_en)
                wcount_q <= wcount_q + 32'd1;

            if (wr_en && (wr_idx == 3'd0)) begin
                if (w_strb_q[0]) ctrl_q[7:0] <= w_data_q[7:0];
                if (w_strb_q[1]) ctrl_q[15:8] <= w_data_q[15:8];
                if (w_strb_q[2]) ctrl_q[23:16] <= w_data_q[23:16];
                if (w_strb_q[3]) ctrl_q[31:24] <= w_data_q[31:24];
            end

            if (wr_en && (wr_idx == 3'd1)) begin
                if (w_strb_q[0]) scratch_q[7:0] <= w_data_q[7:0];
                if (w_strb_q[1]) scratch_q[15:8] <= w_data_q[15:8];
                if (w_strb_q[2]) scratch_q[23:16] <= w_data_q[23:16];
                if (w_strb_q[3]) scratch_q[31:24] <= w_data_q[31:24];
            end

            if (wr_en && (wr_idx == 3'd2)) begin
                if (w_strb_q[0]) config_q[7:0] <= w_data_q[7:0];
                if (w_strb_q[1]) config_q[15:8] <= w_data_q[15:8];
                if (w_strb_q[2]) config_q[23:16] <= w_data_q[23:16];
                if (w_strb_q[3]) config_q[31:24] <= w_data_q[31:24];
            end

            if (wr_en && (wr_idx == 3'd3) && w_strb_q[0])
                mask_q <= w_data_q[7:0];
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            rvalid_q <= 1'b0;
            rdata_q <= 32'd0;
            rresp_q <= 2'b00;
        end else if (arvalid && !rvalid_q) begin
            rvalid_q <= 1'b1;
            rdata_q <= araddr[5] ? 32'd0 : selected_read_data;
            rresp_q <= araddr[5] ? 2'b10 : 2'b00;
        end else if (rvalid_q && rready) begin
            rvalid_q <= 1'b0;
        end
    end
endmodule