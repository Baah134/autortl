`timescale 1ns/1ps
// Qualification reference only: cordic_sincos_tb.v must pass this source and
// fail every mutant in mutants.json. Never configured as a generation seed.
// The top below is byte-identical to the harness's mechanical wrapper.
// @latency 0
// Combinational quadrant pre-rotation: start vector (+-K, 0) and residual angle in 2^-20 turns.
module cordic_prerot (
    input wire [15:0] angle,
    output wire [17:0] x0,
    output wire [19:0] z0
);
    localparam [17:0] K_GAIN = 18'd39797;
    // Quadrants 01 and 10 (|angle| >= 1/4 turn) rotate by half a turn first.
    wire flip = angle[15] ^ angle[14];
    wire [15:0] reduced = {angle[15] ^ flip, angle[14:0]};
    assign x0 = flip ? (18'd0 - K_GAIN) : K_GAIN;
    assign z0 = {reduced, 4'd0};
endmodule

// @latency 0
// Combinational arctangent table: round(atan(2^-idx) * 2^20 / (2*pi)).
module cordic_atan (
    input wire [3:0] idx,
    output reg [19:0] atan
);
    always @(*) begin
        case (idx)
            4'd0: atan = 20'd131072;
            4'd1: atan = 20'd77376;
            4'd2: atan = 20'd40884;
            4'd3: atan = 20'd20753;
            4'd4: atan = 20'd10417;
            4'd5: atan = 20'd5213;
            4'd6: atan = 20'd2607;
            4'd7: atan = 20'd1304;
            4'd8: atan = 20'd652;
            4'd9: atan = 20'd326;
            4'd10: atan = 20'd163;
            4'd11: atan = 20'd81;
            4'd12: atan = 20'd41;
            4'd13: atan = 20'd20;
            4'd14: atan = 20'd10;
            default: atan = 20'd5;
        endcase
    end
endmodule

// @latency 1
// Cycle-level iterative CORDIC rotation engine: one micro-rotation per edge, sixteen edges.
module cordic_engine (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [17:0] x0,
    input wire [19:0] z0,
    input wire [19:0] atan_val,
    output wire [3:0] iter,
    output reg out_valid,
    input wire out_ready,
    output reg [17:0] x,
    output reg [17:0] y
);
    reg busy;
    reg [3:0] i;
    reg [19:0] z;
    wire [17:0] xs = $signed(x) >>> i;
    wire [17:0] ys = $signed(y) >>> i;
    wire rotate_up = !z[19]; // z >= 0

    assign in_ready = !busy && !out_valid;
    assign iter = i;

    always @(posedge clk) begin // engine_clock
        if (rst) begin
            busy <= 1'b0;
            out_valid <= 1'b0;
            i <= 4'd0;
            x <= 18'd0;
            y <= 18'd0;
            z <= 20'd0;
        end else if (busy) begin
            if (rotate_up) begin
                x <= x - ys;
                y <= y + xs;
                z <= z - atan_val;
            end else begin
                x <= x + ys;
                y <= y - xs;
                z <= z + atan_val;
            end
            i <= i + 4'd1;
            if (i == 4'd15) begin
                busy <= 1'b0;
                out_valid <= 1'b1;
            end
        end else if (out_valid) begin
            if (out_ready) out_valid <= 1'b0;
        end else if (in_valid) begin
            x <= x0;
            y <= 18'd0;
            z <= z0;
            i <= 4'd0;
            busy <= 1'b1;
        end
    end
endmodule

// @latency 0
// Combinational output stage: Q2.16 to Q2.14 with round half up, low 16 bits.
module cordic_out (
    input wire [17:0] x_in,
    input wire [17:0] y_in,
    output wire [15:0] cos_out,
    output wire [15:0] sin_out
);
    wire [18:0] x_sum = {x_in[17], x_in} + 19'd2;
    wire [18:0] y_sum = {y_in[17], y_in} + 19'd2;
    assign cos_out = x_sum[17:2];
    assign sin_out = y_sum[17:2];
endmodule

`timescale 1ns/1ps
module cordic_sincos (
    input wire clk,
    input wire rst,
    input wire [15:0] angle,
    input wire in_valid,
    output wire in_ready,
    output wire out_valid,
    input wire out_ready,
    output wire [15:0] cos_out,
    output wire [15:0] sin_out
);
    wire [17:0] w_cordic_prerot_x0;
    wire [19:0] w_cordic_prerot_z0;
    wire [3:0] w_cordic_engine_iter;
    wire [19:0] w_cordic_atan_atan;
    wire [17:0] w_cordic_engine_x;
    wire [17:0] w_cordic_engine_y;
    cordic_prerot u_cordic_prerot (
        .angle(angle),
        .x0(w_cordic_prerot_x0),
        .z0(w_cordic_prerot_z0)
    );
    cordic_atan u_cordic_atan (
        .idx(w_cordic_engine_iter),
        .atan(w_cordic_atan_atan)
    );
    cordic_engine u_cordic_engine (
        .clk(clk),
        .rst(rst),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .x0(w_cordic_prerot_x0),
        .z0(w_cordic_prerot_z0),
        .atan_val(w_cordic_atan_atan),
        .iter(w_cordic_engine_iter),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .x(w_cordic_engine_x),
        .y(w_cordic_engine_y)
    );
    cordic_out u_cordic_out (
        .x_in(w_cordic_engine_x),
        .y_in(w_cordic_engine_y),
        .cos_out(cos_out),
        .sin_out(sin_out)
    );
endmodule
