`timescale 1ns / 1ps
`default_nettype none
// Adapter: spi_master (harness winner, unedited; HALF_PERIOD = 2, so SCLK is
// 25 MHz). The winner's command/response ports are a valid/ready pair
// (cmd_ready = !busy && !rsp_valid), so the shell drives them directly. Its
// SPI pins stay inside the FPGA and connect to a small hand-written mode-0
// slave, so the result is predictable from the transaction:
//   - The slave's transmit register is written with byte 1 when the command
//     is accepted (as the slave's own host would before the transfer).
//   - When cs_n falls, the slave loads its shift register from it and drives
//     the most significant bit on MISO; after each falling SCLK edge it shifts
//     the next bit out. On each rising SCLK edge it samples MOSI into its
//     receive register, most significant bit first.
// The slave watches the winner's registered sclk and cs_n with the same
// clock, so it reacts one clock after each SCLK edge. With HALF_PERIOD = 2
// that leaves MISO settled one clock before the master samples it, and MOSI
// sampled one clock before the master changes it.
// in_word  byte 0 = cmd_data, byte 1 = the byte the slave returns on MISO
// out_word byte 0 = rsp_data (what the master received),
//          byte 1 = what the slave captured from MOSI
module stream_dut (
    input  wire        clk,
    input  wire        rst,
    input  wire [15:0] in_word,
    input  wire        in_valid,
    output wire        in_ready,
    output wire [15:0] out_word,
    output wire        out_valid,
    input  wire        out_ready
);
    wire [7:0] rsp_data;
    wire       sclk, mosi, cs_n;
    wire       miso;

    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    spi_master u_winner (
        .clk(clk), .rst(rst),
        .cmd_data(in_word[7:0]), .cmd_valid(in_valid), .cmd_ready(in_ready),
        .rsp_data(rsp_data), .rsp_valid(out_valid), .rsp_ready(out_ready),
        .sclk(sclk), .mosi(mosi), .miso(miso), .cs_n(cs_n)
    );

    // Mode-0 slave (CPOL = 0, CPHA = 0), 8 bits, most significant bit first.
    reg [7:0] slave_hold;          // the slave's transmit register
    reg [7:0] slave_tx;            // shift register driving MISO
    reg [7:0] slave_rx;            // bits sampled from MOSI
    reg       sclk_q, cs_n_q;
    wire      selected  = !cs_n;
    wire      cs_fall   = cs_n_q && !cs_n;
    wire      sclk_rise = selected && sclk && !sclk_q;
    wire      sclk_fall = selected && !sclk && sclk_q;

    always @(posedge clk) begin
        if (rst) begin
            slave_hold <= 8'd0;
            slave_tx   <= 8'd0;
            slave_rx   <= 8'd0;
            sclk_q     <= 1'b0;
            cs_n_q     <= 1'b1;
        end else begin
            sclk_q <= sclk;
            cs_n_q <= cs_n;
            if (in_valid && in_ready) slave_hold <= in_word[15:8];
            if (cs_fall)              slave_tx   <= slave_hold;
            else if (sclk_fall)       slave_tx   <= {slave_tx[6:0], 1'b0};
            if (sclk_rise)            slave_rx   <= {slave_rx[6:0], mosi};
        end
    end

    assign miso     = slave_tx[7];
    assign out_word = {slave_rx, rsp_data};
endmodule
`default_nettype wire
