`timescale 1ns/1ps
// @latency 1
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
    output wire bvalid,
    input wire bready,
    output wire [1:0] bresp,
    output wire wr_en,
    output wire [2:0] wr_idx,
    output wire [31:0] wr_data,
    output wire [3:0] wr_strb
);

    reg aw_full;
    reg [5:0] aw_addr;
    reg w_full;
    reg [31:0] w_data;
    reg [3:0] w_strb;
    reg b_valid;
    reg [1:0] b_resp;

    wire do_write;

    assign awready = !aw_full;
    assign wready = !w_full;
    assign bvalid = b_valid;
    assign bresp = b_resp;

    assign do_write = aw_full && w_full && !b_valid;
    assign wr_en = do_write && !aw_addr[5];
    assign wr_idx = aw_addr[4:2];
    assign wr_data = w_data;
    assign wr_strb = w_strb;

    always @(posedge clk) begin
        if (rst) begin
            aw_full <= 1'b0;
            aw_addr <= 6'b0;
            w_full <= 1'b0;
            w_data <= 32'b0;
            w_strb <= 4'b0;
            b_valid <= 1'b0;
            b_resp <= 2'b0;
        end else begin
            if (do_write) begin
                aw_full <= 1'b0;
                w_full <= 1'b0;
                b_valid <= 1'b1;
                if (aw_addr[5])
                    b_resp <= 2'b10;
                else
                    b_resp <= 2'b00;
            end else if (b_valid && bready) begin
                b_valid <= 1'b0;
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
`timescale 1ns/1ps
// @latency 1
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

    reg [31:0] ctrl_reg;
    reg [31:0] scratch_reg;
    reg [31:0] config_reg;
    reg [7:0] irq_mask_reg;
    reg [7:0] irq_status_reg;
    reg [31:0] status_reg;
    reg [31:0] write_count_reg;

    always @(posedge clk) begin
        if (rst) begin
            ctrl_reg       <= 32'b0;
            scratch_reg    <= 32'b0;
            config_reg     <= 32'h00000100;
            irq_mask_reg   <= 8'b0;
            irq_status_reg <= 8'b0;
            status_reg     <= 32'b0;
            write_count_reg <= 32'b0;
        end else begin
            status_reg <= status_in;

            irq_status_reg <= (irq_status_reg & ~(
                wr_en && (wr_idx == 3'd4) && wr_strb[0]
                    ? wr_data[7:0] : 8'b0
            )) | irq_set;

            if (wr_en) begin
                write_count_reg <= write_count_reg + 32'd1;

                case (wr_idx)
                    3'd0: begin
                        if (wr_strb[0]) ctrl_reg[7:0]   <= wr_data[7:0];
                        if (wr_strb[1]) ctrl_reg[15:8]  <= wr_data[15:8];
                        if (wr_strb[2]) ctrl_reg[23:16] <= wr_data[23:16];
                        if (wr_strb[3]) ctrl_reg[31:24] <= wr_data[31:24];
                    end
                    3'd1: begin
                        if (wr_strb[0]) scratch_reg[7:0]   <= wr_data[7:0];
                        if (wr_strb[1]) scratch_reg[15:8]  <= wr_data[15:8];
                        if (wr_strb[2]) scratch_reg[23:16] <= wr_data[23:16];
                        if (wr_strb[3]) scratch_reg[31:24] <= wr_data[31:24];
                    end
                    3'd2: begin
                        if (wr_strb[0]) config_reg[7:0]   <= wr_data[7:0];
                        if (wr_strb[1]) config_reg[15:8]  <= wr_data[15:8];
                        if (wr_strb[2]) config_reg[23:16] <= wr_data[23:16];
                        if (wr_strb[3]) config_reg[31:24] <= wr_data[31:24];
                    end
                    3'd3: begin
                        if (wr_strb[0]) irq_mask_reg <= wr_data[7:0];
                    end
                    default: begin
                    end
                endcase
            end
        end
    end

    assign ctrl = ctrl_reg;
    assign irq = |(irq_status_reg & irq_mask_reg);

    assign regs_flat[31:0]    = ctrl_reg;
    assign regs_flat[63:32]   = scratch_reg;
    assign regs_flat[95:64]   = config_reg;
    assign regs_flat[127:96]  = {24'b0, irq_mask_reg};
    assign regs_flat[159:128] = {24'b0, irq_status_reg};
    assign regs_flat[191:160] = status_reg;
    assign regs_flat[223:192] = 32'h52544C35;
    assign regs_flat[255:224] = write_count_reg;

endmodule
`timescale 1ns/1ps
// @latency 1
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

    reg rvalid_reg;
    reg [31:0] rdata_reg;
    reg [1:0] rresp_reg;

    assign arready = !rvalid_reg;
    assign rvalid = rvalid_reg;
    assign rdata = rdata_reg;
    assign rresp = rresp_reg;

    always @(posedge clk) begin
        if (rst) begin
            rvalid_reg <= 1'b0;
            rdata_reg <= 32'b0;
            rresp_reg <= 2'b0;
        end else if (arvalid && !rvalid_reg) begin
            rvalid_reg <= 1'b1;
            if (araddr[5]) begin
                rdata_reg <= 32'b0;
                rresp_reg <= 2'b10;
            end else begin
                rdata_reg <= regs_flat[{araddr[4:2], 5'b0} +: 32];
                rresp_reg <= 2'b00;
            end
        end else if (rvalid_reg && rready) begin
            rvalid_reg <= 1'b0;
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
