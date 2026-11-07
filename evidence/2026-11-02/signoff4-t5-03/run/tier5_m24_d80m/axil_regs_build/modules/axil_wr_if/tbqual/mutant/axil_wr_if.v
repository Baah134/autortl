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
    reg b_valid_reg;
    reg [1:0] b_resp_reg;

    wire do_write;

    assign awready = !aw_full;
    assign wready = !w_full;
    assign bvalid = b_valid_reg;
    assign bresp = b_resp_reg;

    assign do_write = aw_full || w_full && !b_valid_reg;
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
            b_valid_reg <= 1'b0;
            b_resp_reg <= 2'b0;
        end else begin
            if (do_write) begin
                aw_full <= 1'b0;
                w_full <= 1'b0;
                b_valid_reg <= 1'b1;
                b_resp_reg <= aw_addr[5] ? 2'b10 : 2'b00;
            end else if (b_valid_reg && bready) begin
                b_valid_reg <= 1'b0;
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