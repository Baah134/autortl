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
    reg [3:0] w_strobe;
    reg b_valid;
    reg [1:0] b_response;

    wire do_write;

    assign awready = !aw_full;
    assign wready = !w_full;
    assign bvalid = b_valid;
    assign bresp = b_response;

    assign do_write = aw_full && w_full && !b_valid;
    assign wr_en = do_write && !aw_addr[5];
    assign wr_idx = aw_addr[4:2];
    assign wr_data = w_data;
    assign wr_strb = w_strobe;

    always @(posedge clk) begin
        if (rst) begin
            aw_full <= 1'b0;
            aw_addr <= 6'b0;
            w_full <= 1'b0;
            w_data <= 32'b0;
            w_strobe <= 4'b0;
            b_valid <= 1'b0;
            b_response <= 2'b0;
        end else begin
            if (do_write) begin
                aw_full <= 1'b0;
                w_full <= 1'b0;
                b_valid <= 1'b1;
                if (aw_addr[5])
                    b_response <= 2'b10;
                else
                    b_response <= 2'b00;
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
                w_strobe <= wstrb;
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

    reg [31:0] reg_ctrl;
    reg [31:0] reg_scratch;
    reg [31:0] reg_config;
    reg [7:0] irq_mask;
    reg [7:0] irq_status;
    reg [31:0] status_reg;
    reg [31:0] write_count;
    integer b;

    assign regs_flat = {
        write_count,
        32'h52544C35,
        status_reg,
        {24'h000000, irq_status},
        {24'h000000, irq_mask},
        reg_config,
        reg_scratch,
        reg_ctrl
    };

    assign ctrl = reg_ctrl;
    assign irq = |(irq_status & irq_mask);

    always @(posedge clk) begin
        if (rst) begin
            reg_ctrl    <= 32'h00000000;
            reg_scratch <= 32'h00000000;
            reg_config  <= 32'h00000100;
            irq_mask    <= 8'h00;
            irq_status  <= 8'h00;
            status_reg  <= 32'h00000000;
            write_count <= 32'h00000000;
        end else begin
            status_reg <= status_in;
            irq_status <= (irq_status & ~(wr_en && (wr_idx == 3'd4) && wr_strb[0]
                                          ? wr_data[7:0] : 8'h00))
                          | irq_set;

            if (wr_en) begin
                write_count <= write_count + 32'd1;

                case (wr_idx)
                    3'd0: begin
                        for (b = 0; b < 4; b = b + 1)
                            if (wr_strb[b])
                                reg_ctrl[b*8 +: 8] <= wr_data[b*8 +: 8];
                    end
                    3'd1: begin
                        for (b = 0; b < 4; b = b + 1)
                            if (wr_strb[b])
                                reg_scratch[b*8 +: 8] <= wr_data[b*8 +: 8];
                    end
                    3'd2: begin
                        for (b = 0; b < 4; b = b + 1)
                            if (wr_strb[b])
                                reg_config[b*8 +: 8] <= wr_data[b*8 +: 8];
                    end
                    3'd3: begin
                        if (wr_strb[0])
                            irq_mask <= wr_data[7:0];
                    end
                    default: begin
                    end
                endcase
            end
        end
    end

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
                rdata_reg <= regs_flat[araddr[4:2] * 32 +: 32];
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
