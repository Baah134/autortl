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

    assign regs_flat = {
        write_count_reg,
        32'h52544C35,
        status_reg,
        24'b0,
        irq_status_reg,
        24'b0,
        irq_mask_reg,
        config_reg,
        scratch_reg,
        ctrl_reg
    };

    assign ctrl = ctrl_reg;
    assign irq = |(irq_status_reg & irq_mask_reg);

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
                (wr_en && (wr_idx != 3'd4) && wr_strb[0])
                    ? wr_data[7:0]
                    : 8'b0
            )) | irq_set;

            if (wr_en) begin
                write_count_reg <= write_count_reg + 1'b1;

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

endmodule