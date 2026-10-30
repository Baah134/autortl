`timescale 1ns/1ps
// Qualification reference only: spi_master_tb.v must pass this source and
// fail every mutant in mutants.json. Never configured as a generation seed.
// The top below is byte-identical to the harness's mechanical wrapper.
// @latency 33
// Default HALF_PERIOD=2 metadata only; overrides retire no earlier than 16*HALF_PERIOD+1.
module spi_master_core #(parameter HALF_PERIOD = 2) (
    input wire clk,
    input wire rst,
    input wire [7:0] cmd_data,
    input wire cmd_valid,
    output wire cmd_ready,
    output reg [7:0] rsp_data,
    output reg rsp_valid,
    input wire rsp_ready,
    output reg sclk,
    output reg mosi,
    input wire miso,
    output reg cs_n
);
    localparam TICK_BITS = (HALF_PERIOD <= 1) ? 1 : $clog2(HALF_PERIOD);
    reg busy;
    reg [TICK_BITS-1:0] tick;   // clk cycles elapsed in the current SCLK half period
    reg [4:0] half;             // SCLK toggles completed in this transfer (0..16)
    reg [7:0] tx_shift;         // remaining MOSI bits, next bit in [7]
    reg [7:0] rx_shift;         // received MISO bits, first bit ends in [7]

    wire half_done = (tick == HALF_PERIOD - 1);
    wire sample_now = busy && half_done && !sclk;
    assign cmd_ready = !busy && !rsp_valid;

    // MISO is sampled only at the clk edge that raises SCLK.
    always @(posedge clk) begin // rx_sampler
        if (sample_now) rx_shift <= {rx_shift[6:0], miso};
    end

    always @(posedge clk or posedge rst) begin // spi_fsm
        if (rst) begin
            busy <= 1'b0; // reset_busy
            rsp_valid <= 1'b0;
            sclk <= 1'b0;
            mosi <= 1'b0;
            cs_n <= 1'b1;
            tick <= 0;
            half <= 5'd0;
        end else begin
            if (rsp_valid && rsp_ready) rsp_valid <= 1'b0;
            if (!busy) begin
                if (cmd_valid && cmd_ready) begin
                    busy <= 1'b1;
                    cs_n <= 1'b0;
                    mosi <= cmd_data[7];
                    tx_shift <= {cmd_data[6:0], 1'b0};
                    tick <= 0;
                    half <= 5'd0;
                end
            end else if (half_done) begin
                tick <= 0;
                half <= half + 5'd1;
                if (!sclk) begin
                    sclk <= 1'b1; // drive_rise
                end else if (half == 5'd15) begin
                    sclk <= 1'b0;
                    cs_n <= 1'b1;
                    mosi <= 1'b0;
                    busy <= 1'b0;
                    rsp_data <= rx_shift;
                    rsp_valid <= 1'b1;
                end else begin
                    sclk <= 1'b0; // drive_fall
                    mosi <= tx_shift[7];
                    tx_shift <= {tx_shift[6:0], 1'b0};
                end
            end else begin
                tick <= tick + 1'b1;
            end
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
