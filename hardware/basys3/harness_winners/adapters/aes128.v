`timescale 1ns / 1ps
`default_nettype none
// Adapter: aes128_core (harness winner, unedited). The winner has its own
// valid/ready handshake (in_ready = !busy && !out_valid), so the adapter only
// maps bytes. The shell puts transaction byte n at in_word[8n+7:8n]; the
// winner's 128-bit ports are big-endian (FIPS byte n = bits [127-8n -: 8]).
// in_word  bytes 0..15  = key bytes 0..15 (FIPS order)
//          bytes 16..31 = plaintext bytes 0..15
// out_word bytes 0..15  = ciphertext bytes 0..15
module stream_dut (
    input  wire         clk,
    input  wire         rst,
    input  wire [255:0] in_word,
    input  wire         in_valid,
    output wire         in_ready,
    output wire [127:0] out_word,
    output wire         out_valid,
    input  wire         out_ready
);
    wire [127:0] key, pt, ct;

    genvar n;
    generate
        for (n = 0; n < 16; n = n + 1) begin : g_bytes
            assign key[127 - 8*n -: 8] = in_word[8*n +: 8];
            assign pt[127 - 8*n -: 8]  = in_word[128 + 8*n +: 8];
            assign out_word[8*n +: 8]  = ct[127 - 8*n -: 8];
        end
    endgenerate

    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    aes128_core u_winner (
        .clk(clk), .rst(rst),
        .in_valid(in_valid), .in_ready(in_ready),
        .key(key), .pt(pt),
        .out_valid(out_valid), .out_ready(out_ready),
        .ct(ct)
    );
endmodule
`default_nettype wire
