`timescale 1ns / 1ps
`default_nettype none
// Adapter: dot4_pipeline (harness winner, unedited). The winner is a
// fixed-latency pipeline with no handshake: a tuple applied before rising
// edge k has its result on dot_result after edge k+1 (latency 2). The
// adapter tags accepted tuples through a 2-deep valid shift register,
// captures each result into a 4-entry skid FIFO, and only accepts a new
// tuple when a FIFO slot is guaranteed (credits = in flight + stored < 4).
// in_word  bytes 0..7 = a0, b0, a1, b1, a2, b2, a3, b3 (unsigned)
// out_word = 18-bit unsigned dot product, zero-extended to 24 bits
module stream_dut (
    input  wire        clk,
    input  wire        rst,
    input  wire [63:0] in_word,
    input  wire        in_valid,
    output wire        in_ready,
    output wire [23:0] out_word,
    output wire        out_valid,
    input  wire        out_ready
);
    localparam LATENCY = 2;
    localparam SLOTS   = 4;

    wire [17:0] dot;

    // Keep the winner's boundary so its own resources are reported and can be
    // compared with the harness's measurement of the same file.
    (* keep_hierarchy = "yes" *)
    dot4_pipeline u_winner (
        .clk(clk), .rst(rst),
        .a0(in_word[7:0]),   .b0(in_word[15:8]),
        .a1(in_word[23:16]), .b1(in_word[31:24]),
        .a2(in_word[39:32]), .b2(in_word[47:40]),
        .a3(in_word[55:48]), .b3(in_word[63:56]),
        .dot_result(dot)
    );

    reg [LATENCY-1:0] tag;
    reg [2:0]         credits_used;
    wire              accept = in_valid && in_ready;
    wire              retire = out_valid && out_ready;
    wire              empty;

    assign in_ready  = credits_used < SLOTS;
    assign out_valid = !empty;

    always @(posedge clk) begin
        if (rst) begin
            tag          <= {LATENCY{1'b0}};
            credits_used <= 3'd0;
        end else begin
            tag          <= {tag[LATENCY-2:0], accept};
            credits_used <= credits_used + accept - retire;
        end
    end

    wire [23:0] fifo_dout;
    wire        full;

    shell_fifo #(.WIDTH(24), .DEPTH_LOG2(2)) u_skid (
        .clk(clk), .rst(rst),
        .wr_en(tag[LATENCY-1]), .din({6'd0, dot}),
        .rd_en(retire), .dout(fifo_dout),
        .empty(empty), .full(full)
    );

    assign out_word = fifo_dout;
endmodule
`default_nettype wire
