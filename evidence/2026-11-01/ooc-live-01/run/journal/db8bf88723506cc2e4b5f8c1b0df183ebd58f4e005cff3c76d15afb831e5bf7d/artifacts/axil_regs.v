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
    output reg bvalid,
    input wire bready,
    output reg [1:0] bresp,
    input wire arvalid,
    output wire arready,
    input wire [5:0] araddr,
    output reg rvalid,
    input wire rready,
    output reg [31:0] rdata,
    output reg [1:0] rresp,
    input wire [7:0] irq_set,
    input wire [31:0] status_in,
    output wire [31:0] ctrl,
    output wire irq
);
    localparam [31:0] ID_VALUE = 32'h52544C35;

    reg aw_full;
    reg w_full;
    reg [5:0] aw_addr_q;
    reg [31:0] w_data_q;
    reg [3:0] w_strb_q;

    reg [31:0] ctrl_q;
    reg [31:0] scratch_q;
    reg [31:0] config_q;
    reg [31:0] status_q;
    reg [31:0] wcount_q;
    reg [7:0] mask_q;
    reg [7:0] pend_q;

    wire do_write = aw_full && w_full && !bvalid;
    wire wr_en = do_write && !aw_addr_q[5];
    wire [2:0] wr_idx = aw_addr_q[4:2];
    wire [7:0] w1c_clear =
        (wr_en && (wr_idx == 3'd4) && w_strb_q[0]) ?
        w_data_q[7:0] : 8'd0;

    wire [31:0] read_selected;
    assign read_selected =
        (araddr[4:2] == 3'd0) ? ctrl_q :
        (araddr[4:2] == 3'd1) ? scratch_q :
        (araddr[4:2] == 3'd2) ? config_q :
        (araddr[4:2] == 3'd3) ? {24'd0, mask_q} :
        (araddr[4:2] == 3'd4) ? {24'd0, pend_q} :
        (araddr[4:2] == 3'd5) ? status_q :
        (araddr[4:2] == 3'd6) ? ID_VALUE :
                                wcount_q;

    assign awready = !aw_full;
    assign wready = !w_full;
    assign arready = !rvalid;
    assign ctrl = ctrl_q;
    assign irq = |(pend_q & mask_q);

    always @(posedge clk) begin
        if (rst) begin
            aw_full <= 1'b0;
            w_full <= 1'b0;
            aw_addr_q <= 6'd0;
            w_data_q <= 32'd0;
            w_strb_q <= 4'd0;
            bvalid <= 1'b0;
            bresp <= 2'b00;
        end else begin
            if (do_write) begin
                aw_full <= 1'b0;
                w_full <= 1'b0;
                bvalid <= 1'b1;
                bresp <= aw_addr_q[5] ? 2'b10 : 2'b00;
            end else if (bvalid && bready) begin
                bvalid <= 1'b0;
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
            status_q <= 32'd0;
            wcount_q <= 32'd0;
            mask_q <= 8'd0;
            pend_q <= 8'd0;
        end else begin
            status_q <= status_in;
            pend_q <= (pend_q & ~w1c_clear) | irq_set;

            if (wr_en) begin
                wcount_q <= wcount_q + 32'd1;

                case (wr_idx)
                    3'd0: begin
                        if (w_strb_q[0]) ctrl_q[7:0]   <= w_data_q[7:0];
                        if (w_strb_q[1]) ctrl_q[15:8]  <= w_data_q[15:8];
                        if (w_strb_q[2]) ctrl_q[23:16] <= w_data_q[23:16];
                        if (w_strb_q[3]) ctrl_q[31:24] <= w_data_q[31:24];
                    end
                    3'd1: begin
                        if (w_strb_q[0]) scratch_q[7:0]   <= w_data_q[7:0];
                        if (w_strb_q[1]) scratch_q[15:8]  <= w_data_q[15:8];
                        if (w_strb_q[2]) scratch_q[23:16] <= w_data_q[23:16];
                        if (w_strb_q[3]) scratch_q[31:24] <= w_data_q[31:24];
                    end
                    3'd2: begin
                        if (w_strb_q[0]) config_q[7:0]   <= w_data_q[7:0];
                        if (w_strb_q[1]) config_q[15:8]  <= w_data_q[15:8];
                        if (w_strb_q[2]) config_q[23:16] <= w_data_q[23:16];
                        if (w_strb_q[3]) config_q[31:24] <= w_data_q[31:24];
                    end
                    3'd3: begin
                        if (w_strb_q[0]) mask_q <= w_data_q[7:0];
                    end
                    default: begin
                    end
                endcase
            end
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            rvalid <= 1'b0;
            rdata <= 32'd0;
            rresp <= 2'b00;
        end else if (arvalid && !rvalid) begin
            rvalid <= 1'b1;
            rdata <= araddr[5] ? 32'd0 : read_selected;
            rresp <= araddr[5] ? 2'b10 : 2'b00;
        end else if (rvalid && rready) begin
            rvalid <= 1'b0;
        end
    end
endmodule