`timescale 1ns/1ps
// Qualification reference only: fir16_sym_tb.v must pass this source and
// fail every mutant in mutants.json. Never configured as a generation seed.
// The top below is byte-identical to the harness's mechanical wrapper.
// @latency 5
// Minimum accepted-transfer age through five elastic slots; exact when out_ready stays high.
module fir16_sym_core (
    input wire clk,
    input wire rst,
    input wire signed [15:0] in_sample,
    input wire in_valid,
    output wire in_ready,
    output reg signed [15:0] out_sample,
    output wire out_valid,
    input wire out_ready
);
    // h[k] = h[15-k]; the eight unique taps sum to 1024, so the DC gain is 2048 (unity after >>> 11).
    localparam signed [9:0] H0 = -10'sd6;
    localparam signed [9:0] H1 = -10'sd20;
    localparam signed [9:0] H2 = -10'sd24;
    localparam signed [9:0] H3 = 10'sd18;
    localparam signed [9:0] H4 = 10'sd110;
    localparam signed [9:0] H5 = 10'sd226;
    localparam signed [9:0] H6 = 10'sd330;
    localparam signed [9:0] H7 = 10'sd390;

    reg signed [15:0] tap [0:15];     // slot 1: accepted history, tap[0] newest
    reg signed [16:0] pre [0:7];      // slot 2: symmetric pre-adder sums
    reg signed [26:0] prod [0:7];     // slot 3: products
    reg signed [28:0] sum_lo, sum_hi; // slot 4: partial sums
    reg v1, v2, v3, v4, v5;
    integer i;

    wire r5 = !v5 || out_ready;
    wire r4 = !v4 || r5;
    wire r3 = !v3 || r4;
    wire r2 = !v2 || r3;
    wire r1 = !v1 || r2;
    assign in_ready = r1;
    assign out_valid = v5;
    wire accept = in_valid && r1;

    wire signed [29:0] total = sum_lo + sum_hi + 30'sd1024; // round half up
    wire signed [18:0] scaled = total >>> 11;
    wire signed [15:0] y_next = (scaled > 19'sd32767) ? 16'sh7fff :
                                (scaled < -19'sd32768) ? 16'sh8000 : scaled[15:0];

    always @(posedge clk) begin // fir_pipe
        if (rst) begin
            v1 <= 1'b0;
            v2 <= 1'b0;
            v3 <= 1'b0;
            v4 <= 1'b0;
            v5 <= 1'b0;
            for (i = 0; i < 16; i = i + 1)
                tap[i] <= 16'sd0; // clear_history
        end else begin
            if (r5) begin
                v5 <= v4;
                if (v4) out_sample <= y_next;
            end
            if (r4) begin
                v4 <= v3;
                if (v3) begin
                    sum_lo <= prod[0] + prod[1] + prod[2] + prod[3];
                    sum_hi <= prod[4] + prod[5] + prod[6] + prod[7];
                end
            end
            if (r3) begin
                v3 <= v2;
                if (v2) begin
                    prod[0] <= pre[0] * H0;
                    prod[1] <= pre[1] * H1;
                    prod[2] <= pre[2] * H2;
                    prod[3] <= pre[3] * H3;
                    prod[4] <= pre[4] * H4;
                    prod[5] <= pre[5] * H5;
                    prod[6] <= pre[6] * H6;
                    prod[7] <= pre[7] * H7;
                end
            end
            if (r2) begin
                v2 <= v1;
                if (v1) begin
                    pre[0] <= tap[0] + tap[15];
                    pre[1] <= tap[1] + tap[14];
                    pre[2] <= tap[2] + tap[13];
                    pre[3] <= tap[3] + tap[12];
                    pre[4] <= tap[4] + tap[11];
                    pre[5] <= tap[5] + tap[10];
                    pre[6] <= tap[6] + tap[9];
                    pre[7] <= tap[7] + tap[8];
                end
            end
            if (r1) v1 <= in_valid;
            if (accept) begin // history_shift
                tap[0] <= in_sample;
                for (i = 1; i < 16; i = i + 1)
                    tap[i] <= tap[i-1];
            end
        end
    end
endmodule

`timescale 1ns/1ps
// @latency 5
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
module fir16_sym (
    input wire clk,
    input wire rst,
    input wire signed [15:0] in_sample,
    input wire in_valid,
    output wire in_ready,
    output wire signed [15:0] out_sample,
    output wire out_valid,
    input wire out_ready
);
    fir16_sym_core u_fir16_sym_core (
        .clk(clk),
        .rst(rst),
        .in_sample(in_sample),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_sample(out_sample),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule
