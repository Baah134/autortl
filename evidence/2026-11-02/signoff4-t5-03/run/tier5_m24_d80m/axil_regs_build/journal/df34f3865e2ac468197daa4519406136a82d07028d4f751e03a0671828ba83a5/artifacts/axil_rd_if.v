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
        end else if (arvalid || !rvalid_reg) begin
            rvalid_reg <= 1'b1;
            if (araddr[5]) begin
                rdata_reg <= 32'b0;
                rresp_reg <= 2'b10;
            end else begin
                case (araddr[4:2])
                    3'd0: rdata_reg <= regs_flat[31:0];
                    3'd1: rdata_reg <= regs_flat[63:32];
                    3'd2: rdata_reg <= regs_flat[95:64];
                    3'd3: rdata_reg <= regs_flat[127:96];
                    3'd4: rdata_reg <= regs_flat[159:128];
                    3'd5: rdata_reg <= regs_flat[191:160];
                    3'd6: rdata_reg <= regs_flat[223:192];
                    3'd7: rdata_reg <= regs_flat[255:224];
                endcase
                rresp_reg <= 2'b00;
            end
        end else if (rvalid_reg && rready) begin
            rvalid_reg <= 1'b0;
        end
    end

endmodule