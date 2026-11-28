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

    reg busy_reg;
    reg rsp_valid_reg;
    reg sclk_reg;
    reg mosi_reg;
    reg cs_n_reg;
    reg [3:0] half_count;
    reg [3:0] toggle_count;
    reg [7:0] tx_shift;
    reg [7:0] rx_shift;

    assign cmd_ready = !busy_reg && !rsp_valid_reg;
    assign rsp_data = rx_shift;
    assign rsp_valid = rsp_valid_reg;
    assign sclk = sclk_reg;
    assign mosi = mosi_reg;
    assign cs_n = cs_n_reg;

    always @(posedge clk) begin
        if (rst) begin
            busy_reg <= 1'b0;
            rsp_valid_reg <= 1'b0;
            sclk_reg <= 1'b0;
            mosi_reg <= 1'b0;
            cs_n_reg <= 1'b1;
            half_count <= 4'b0;
            toggle_count <= 4'b0;
            tx_shift <= 8'b0;
            rx_shift <= 8'b0;
        end else if (busy_reg) begin
            if (half_count == 0) begin
                half_count <= HALF_PERIOD - 1;
                if (toggle_count == 15) begin
                    busy_reg <= 1'b0;
                    rsp_valid_reg <= 1'b1;
                    sclk_reg <= 1'b0;
                    mosi_reg <= 1'b0;
                    cs_n_reg <= 1'b1;
                end else begin
                    toggle_count <= toggle_count + 1'b1;
                    sclk_reg <= ~sclk_reg;
                    if (toggle_count[0] == 1'b0) begin
                        rx_shift <= {rx_shift[6:0], miso};
                    end else begin
                        mosi_reg <= tx_shift[7];
                        tx_shift <= {tx_shift[6:0], 1'b0};
                    end
                end
            end else begin
                half_count <= half_count - 1'b1;
            end
        end else if (rsp_valid_reg) begin
            if (rsp_ready)
                rsp_valid_reg <= 1'b0;
        end else if (cmd_valid) begin
            busy_reg <= 1'b1;
            half_count <= HALF_PERIOD - 1;
            toggle_count <= 4'b0;
            tx_shift <= {cmd_data[6:0], 1'b0};
            rx_shift <= 8'b0;
            sclk_reg <= 1'b0;
            mosi_reg <= cmd_data[7];
            cs_n_reg <= 1'b0;
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 33
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
    spi_master_core #(.HALF_PERIOD(2)) u_spi_master_core (
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
        .cs_n(cs_n),
        .miso(miso)
    );
endmodule