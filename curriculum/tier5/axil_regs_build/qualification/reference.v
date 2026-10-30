`timescale 1ns/1ps
// Qualification reference only: axil_regs_tb.v must pass this source and
// fail every mutant in mutants.json. Never configured as a generation seed.
// The top below is byte-identical to the harness's mechanical wrapper.
// @latency 1
// Cycle-level: awready, wready and the wr_* bank port are views of registered state.
module axil_wr_if (
    input wire clk,
    input wire rst,
    input wire awvalid,
    output wire awready,
    input wire [5:0] awaddr,
    input wire wvalid,
    output wire wready,
    input wire [31:0] wdata,
    input wire [3:0] wstrb,
    output reg bvalid,
    input wire bready,
    output reg [1:0] bresp,
    output wire wr_en,
    output wire [2:0] wr_idx,
    output wire [31:0] wr_data,
    output wire [3:0] wr_strb
);
    reg aw_full, w_full;     // one held address and one held data beat
    reg [5:0] aw_addr;
    reg [31:0] w_data;
    reg [3:0] w_strb;

    // Both halves held and no response pending: write and respond at this edge.
    wire do_write = aw_full && w_full && !bvalid;
    assign awready = !aw_full;
    assign wready = !w_full;
    assign wr_en = do_write && !aw_addr[5];
    assign wr_idx = aw_addr[4:2];
    assign wr_data = w_data;
    assign wr_strb = w_strb;

    always @(posedge clk) begin // wr_clock
        if (rst) begin
            aw_full <= 1'b0;
            w_full <= 1'b0;
            aw_addr <= 6'd0;
            w_data <= 32'd0;
            w_strb <= 4'd0;
            bvalid <= 1'b0;
            bresp <= 2'b00;
        end else begin
            if (do_write) begin
                aw_full <= 1'b0;
                w_full <= 1'b0;
                bvalid <= 1'b1;
                bresp <= aw_addr[5] ? 2'b10 : 2'b00;
            end else if (bvalid && bready) begin
                bvalid <= 1'b0;
            end
            if (awvalid && awready) begin
                aw_full <= 1'b1;
                aw_addr <= awaddr;
            end
            if (wvalid && wready) begin
                w_full <= 1'b1;
                w_data <= wdata;
                w_strb <= wstrb;
            end
        end
    end
endmodule

// @latency 1
// Cycle-level: regs_flat, ctrl and irq are views of registered state.
module axil_regbank (
    input wire clk,
    input wire rst,
    input wire wr_en,
    input wire [2:0] wr_idx,
    input wire [31:0] wr_data,
    input wire [3:0] wr_strb,
    input wire [7:0] irq_set,
    input wire [31:0] status_in,
    output wire [255:0] regs_flat,
    output wire [31:0] ctrl,
    output wire irq
);
    localparam [31:0] ID_VALUE = 32'h52544C35;
    reg [31:0] ctrl_q, scratch_q, config_q, status_q, wcount_q;
    reg [7:0] mask_q, pend_q;

    wire [31:0] strobe_mask = {{8{wr_strb[3]}}, {8{wr_strb[2]}}, {8{wr_strb[1]}}, {8{wr_strb[0]}}};
    wire [31:0] merged_ctrl = (ctrl_q & ~strobe_mask) | (wr_data & strobe_mask);
    wire [31:0] merged_scratch = (scratch_q & ~strobe_mask) | (wr_data & strobe_mask);
    wire [31:0] merged_config = (config_q & ~strobe_mask) | (wr_data & strobe_mask);
    wire [7:0] w1c_clear = (wr_en && wr_idx == 3'd4 && wr_strb[0]) ? wr_data[7:0] : 8'd0;

    always @(posedge clk) begin // bank_clock
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
            pend_q <= (pend_q & ~w1c_clear) | irq_set; // set_wins
            if (wr_en) begin
                wcount_q <= wcount_q + 32'd1;
                case (wr_idx)
                    3'd0: ctrl_q <= merged_ctrl;
                    3'd1: scratch_q <= merged_scratch;
                    3'd2: config_q <= merged_config;
                    3'd3: if (wr_strb[0]) mask_q <= wr_data[7:0];
                    default: ; // 4 is write-1-to-clear above; 5, 6 and 7 are read-only
                endcase
            end
        end
    end

    assign regs_flat = {wcount_q, ID_VALUE, status_q, {24'd0, pend_q}, {24'd0, mask_q},
                        config_q, scratch_q, ctrl_q};
    assign ctrl = ctrl_q;
    assign irq = |(pend_q & mask_q);
endmodule

// @latency 1
// Cycle-level: arready is a view of registered state.
module axil_rd_if (
    input wire clk,
    input wire rst,
    input wire arvalid,
    output wire arready,
    input wire [5:0] araddr,
    output reg rvalid,
    input wire rready,
    output reg [31:0] rdata,
    output reg [1:0] rresp,
    input wire [255:0] regs_flat
);
    wire [31:0] selected = regs_flat[araddr[4:2]*32 +: 32];
    assign arready = !rvalid;

    always @(posedge clk) begin // rd_clock
        if (rst) begin
            rvalid <= 1'b0;
            rdata <= 32'd0;
            rresp <= 2'b00;
        end else if (arvalid && !rvalid) begin // ar_handshake
            rvalid <= 1'b1;
            rdata <= araddr[5] ? 32'd0 : selected;
            rresp <= araddr[5] ? 2'b10 : 2'b00;
        end else if (rvalid && rready) begin
            rvalid <= 1'b0;
        end
    end
endmodule

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
