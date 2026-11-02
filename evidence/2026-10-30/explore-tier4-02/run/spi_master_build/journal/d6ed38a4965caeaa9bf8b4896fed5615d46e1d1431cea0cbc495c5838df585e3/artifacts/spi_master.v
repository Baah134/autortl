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
    reg rsp_valid_reg;
    reg [7:0] rsp_data_reg;
    reg sclk_reg;
    reg mosi_reg;
    reg cs_n_reg;
    reg [7:0] tx_shift;
    reg [7:0] rx_shift;
    reg [3:0] phase_count;
    reg [4:0] toggle_count;

    assign cmd_ready = !busy && !rsp_valid_reg;
    assign rsp_valid = rsp_valid_reg;
    assign rsp_data = rsp_data_reg;
    assign sclk = sclk_reg;
    assign mosi = mosi_reg;
    assign cs_n = cs_n_reg;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            rsp_valid_reg <= 1'b0;
            rsp_data_reg <= 8'b0;
            sclk_reg <= 1'b0;
            mosi_reg <= 1'b0;
            cs_n_reg <= 1'b1;
            tx_shift <= 8'b0;
            rx_shift <= 8'b0;
            phase_count <= 4'b0;
            toggle_count <= 5'b0;
        end else if (busy) begin
            if (phase_count == HALF_PERIOD - 1) begin
                phase_count <= 4'b0;
                sclk_reg <= ~sclk_reg;

                if (toggle_count == 5'd15) begin
                    busy <= 1'b0;
                    cs_n_reg <= 1'b1;
                    sclk_reg <= 1'b0;
                    mosi_reg <= 1'b0;
                    rsp_data_reg <= rx_shift;
                    rsp_valid_reg <= 1'b1;
                    toggle_count <= 5'b0;
                end else begin
                    toggle_count <= toggle_count + 1'b1;
                    if (!toggle_count[0]) begin
                        rx_shift <= {rx_shift[6:0], miso};
                    end else begin
                        tx_shift <= {tx_shift[6:0], 1'b0};
                        mosi_reg <= tx_shift[6];
                    end
                end
            end else begin
                phase_count <= phase_count + 1'b1;
            end
        end else if (rsp_valid_reg) begin
            if (rsp_ready)
                rsp_valid_reg <= 1'b0;
        end else if (cmd_valid) begin
            busy <= 1'b1;
            cs_n_reg <= 1'b0;
            sclk_reg <= 1'b0;
            mosi_reg <= cmd_data[7];
            tx_shift <= cmd_data;
            rx_shift <= 8'b0;
            phase_count <= 4'b0;
            toggle_count <= 5'b0;
        end
    end

endmodule
`timescale 1ns/1ps
// @latency 33
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
module spi_master (
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
    spi_master_core #( .HALF_PERIOD(2) ) u_spi_master_core (
        .clk(clk),
        .rst(rst),
        .cmd_data(cmd_data),
        .cmd_valid(cmd_valid),
        .cmd_ready(cmd_ready),
        .rsp_data(rsp_data),
        .rsp_valid(rsp_valid),
        .rsp_ready(rsp_ready),
        .sclk(sclk),
        .mosi(mosi),
        .miso(miso),
        .cs_n(cs_n)
    );
endmodule
