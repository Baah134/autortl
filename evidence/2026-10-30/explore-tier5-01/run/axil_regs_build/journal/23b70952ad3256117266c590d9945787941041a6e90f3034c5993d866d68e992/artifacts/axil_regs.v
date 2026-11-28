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
    localparam [31:0] ID_VALUE = 32'h52544c35;

    reg aw_pending;
    reg [5:0] awaddr_hold;
    reg w_pending;
    reg [31:0] wdata_hold;
    reg [3:0] wstrb_hold;

    reg [31:0] ctrl_reg;
    reg [7:0] irq_status;
    reg [7:0] irq_enable;

    wire write_active;
    wire [5:0] write_addr;
    wire [31:0] write_data;
    wire [3:0] write_strb;
    wire [31:0] read_value;
    wire read_valid_addr;

    assign awready = !aw_pending && !bvalid;
    assign wready = !w_pending && !bvalid;
    assign arready = !rvalid || rready;

    assign write_active = !bvalid &&
                          (aw_pending || (awvalid && awready)) &&
                          (w_pending || (wvalid && wready));
    assign write_addr = aw_pending ? awaddr_hold : awaddr;
    assign write_data = w_pending ? wdata_hold : wdata;
    assign write_strb = w_pending ? wstrb_hold : wstrb;

    assign read_valid_addr = (araddr[1:0] == 2'b00) &&
                             (araddr[5:5] == 1'b0);
    assign read_value =
        (araddr[4:2] == 3'd0) ? ctrl_reg :
        (araddr[4:2] == 3'd1) ? status_in :
        (araddr[4:2] == 3'd2) ? {24'b0, irq_status} :
        (araddr[4:2] == 3'd3) ? {24'b0, irq_enable} :
        (araddr[4:2] == 3'd4) ? ID_VALUE :
                                32'b0;

    assign ctrl = ctrl_reg;
    assign irq = |(irq_status & irq_enable);

    always @(posedge clk) begin
        if (rst) begin
            aw_pending <= 1'b0;
            awaddr_hold <= 6'b0;
            w_pending <= 1'b0;
            wdata_hold <= 32'b0;
            wstrb_hold <= 4'b0;
            bvalid <= 1'b0;
            bresp <= 2'b00;
            rvalid <= 1'b0;
            rdata <= 32'b0;
            rresp <= 2'b00;
            ctrl_reg <= 32'b0;
            irq_status <= 8'b0;
            irq_enable <= 8'b0;
        end else begin
            if (bvalid && bready)
                bvalid <= 1'b0;

            if (awvalid && awready) begin
                aw_pending <= 1'b1;
                awaddr_hold <= awaddr;
            end

            if (wvalid && wready) begin
                w_pending <= 1'b1;
                wdata_hold <= wdata;
                wstrb_hold <= wstrb;
            end

            if (write_active) begin
                aw_pending <= 1'b0;
                w_pending <= 1'b0;
                bvalid <= 1'b1;
                if ((write_addr[1:0] == 2'b00) && !write_addr[5]) begin
                    bresp <= 2'b00;
                    case (write_addr[4:2])
                        3'd0: begin
                            if (write_strb[0]) ctrl_reg[7:0]   <= write_data[7:0];
                            if (write_strb[1]) ctrl_reg[15:8]  <= write_data[15:8];
                            if (write_strb[2]) ctrl_reg[23:16] <= write_data[23:16];
                            if (write_strb[3]) ctrl_reg[31:24] <= write_data[31:24];
                        end
                        3'd2: begin
                            if (write_strb[0])
                                irq_status[7:0] <= (irq_status[7:0] & ~write_data[7:0]) | irq_set;
                            else
                                irq_status[7:0] <= irq_status[7:0] | irq_set;
                        end
                        3'd3: begin
                            if (write_strb[0]) irq_enable[7:0] <= write_data[7:0];
                        end
                        default: begin
                        end
                    endcase
                end else begin
                    bresp <= 2'b10;
                end
            end else begin
                irq_status <= irq_status | irq_set;
            end

            if (arvalid && arready) begin
                rvalid <= 1'b1;
                rdata <= read_valid_addr ? read_value : 32'b0;
                rresp <= read_valid_addr ? 2'b00 : 2'b10;
            end else if (rvalid && rready) begin
                rvalid <= 1'b0;
            end
        end
    end
endmodule