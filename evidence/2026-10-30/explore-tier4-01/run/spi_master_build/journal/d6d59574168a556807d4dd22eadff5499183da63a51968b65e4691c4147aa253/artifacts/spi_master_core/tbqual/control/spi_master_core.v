`timescale 1ns/1ps
// @latency 33
module spi_master_core #(
    parameter HALF_PERIOD = 2
) (
    input wire clk,
    input wire rst,
    input wire [7:0] cmd_data,
    input wire cmd_valid,
    output wire cmd_ready,
    output wire [7:0] rsp_data,
    output wire rsp_valid,
    input wire rsp_ready,
    output wire sclk,
    output wire mosi,
    input wire miso,
    output wire cs_n
);

    reg busy;
    reg [2:0] div_count;
    reg [4:0] phase_count;
    reg [7:0] tx_shift;
    reg [7:0] rx_shift;
    reg [7:0] rsp_data_reg;
    reg rsp_valid_reg;
    reg sclk_reg;
    reg mosi_reg;
    reg cs_n_reg;

    assign cmd_ready = !busy && !rsp_valid_reg;
    assign rsp_data = rsp_data_reg;
    assign rsp_valid = rsp_valid_reg;
    assign sclk = sclk_reg;
    assign mosi = mosi_reg;
    assign cs_n = cs_n_reg;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            div_count <= 3'd0;
            phase_count <= 5'd0;
            tx_shift <= 8'd0;
            rx_shift <= 8'd0;
            rsp_data_reg <= 8'd0;
            rsp_valid_reg <= 1'b0;
            sclk_reg <= 1'b0;
            mosi_reg <= 1'b0;
            cs_n_reg <= 1'b1;
        end else begin
            if (rsp_valid_reg && rsp_ready)
                rsp_valid_reg <= 1'b0;

            if (!busy && !rsp_valid_reg && cmd_valid) begin
                busy <= 1'b1;
                div_count <= 3'd0;
                phase_count <= 5'd0;
                tx_shift <= cmd_data;
                rx_shift <= 8'd0;
                sclk_reg <= 1'b0;
                mosi_reg <= cmd_data[7];
                cs_n_reg <= 1'b0;
            end else if (busy) begin
                if (div_count == HALF_PERIOD - 1) begin
                    div_count <= 3'd0;

                    if (phase_count[0]) begin
                        sclk_reg <= 1'b0;
                        if (phase_count == 5'd15) begin
                            busy <= 1'b0;
                            cs_n_reg <= 1'b1;
                            mosi_reg <= 1'b0;
                            rsp_data_reg <= rx_shift;
                            rsp_valid_reg <= 1'b1;
                        end else begin
                            mosi_reg <= tx_shift[6];
                            tx_shift <= {tx_shift[6:0], 1'b0};
                        end
                    end else begin
                        sclk_reg <= 1'b1;
                        rx_shift <= {rx_shift[6:0], miso};
                    end

                    phase_count <= phase_count + 1'b1;
                end else begin
                    div_count <= div_count + 1'b1;
                end
            end
        end
    end

endmodule