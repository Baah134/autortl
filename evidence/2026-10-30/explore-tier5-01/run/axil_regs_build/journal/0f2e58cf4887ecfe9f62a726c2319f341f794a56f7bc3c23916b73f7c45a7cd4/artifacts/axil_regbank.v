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
        32'h00000000,
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