`timescale 1ns/1ps
// @latency 0
module cordic_prerot (
    input  wire [15:0] angle,
    output wire [17:0] x0,
    output wire [19:0] z0
);

    wire flip;
    wire [15:0] reduced_angle;

    assign flip = angle[15] ^ angle[14];
    assign reduced_angle = angle ^ (flip ? 16'h8000 : 16'h0000);
    assign x0 = flip ? 18'd222347 : 18'd39797;
    assign z0 = {reduced_angle, 4'b0000};

endmodule
`timescale 1ns/1ps
// @latency 0
module cordic_atan (
    input  wire [3:0]  idx,
    output wire [19:0] atan
);

    reg [19:0] atan_value;

    always @(*) begin
        atan_value = 20'd0;
        case (idx)
            4'd0:  atan_value = 20'd131072;
            4'd1:  atan_value = 20'd77376;
            4'd2:  atan_value = 20'd40884;
            4'd3:  atan_value = 20'd20753;
            4'd4:  atan_value = 20'd10417;
            4'd5:  atan_value = 20'd5213;
            4'd6:  atan_value = 20'd2607;
            4'd7:  atan_value = 20'd1304;
            4'd8:  atan_value = 20'd652;
            4'd9:  atan_value = 20'd326;
            4'd10: atan_value = 20'd163;
            4'd11: atan_value = 20'd81;
            4'd12: atan_value = 20'd41;
            4'd13: atan_value = 20'd20;
            4'd14: atan_value = 20'd10;
            4'd15: atan_value = 20'd5;
        endcase
    end

    assign atan = atan_value;

endmodule
`timescale 1ns/1ps
// @latency 1
module cordic_engine (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [17:0] x0,
    input wire [19:0] z0,
    input wire [19:0] atan_val,
    output wire [3:0] iter,
    output wire out_valid,
    input wire out_ready,
    output wire [17:0] x,
    output wire [17:0] y
);

    reg busy_reg;
    reg out_valid_reg;
    reg [3:0] i_reg;
    reg signed [17:0] x_reg;
    reg signed [17:0] y_reg;
    reg [19:0] z_reg;

    wire signed [17:0] x_shift;
    wire signed [17:0] y_shift;

    assign x_shift = x_reg >>> i_reg;
    assign y_shift = y_reg >>> i_reg;

    assign in_ready = !busy_reg && !out_valid_reg;
    assign out_valid = out_valid_reg;
    assign iter = i_reg;
    assign x = x_reg;
    assign y = y_reg;

    always @(posedge clk) begin
        if (rst) begin
            busy_reg <= 1'b0;
            out_valid_reg <= 1'b0;
            i_reg <= 4'd0;
            x_reg <= 18'd0;
            y_reg <= 18'd0;
            z_reg <= 20'd0;
        end else if (busy_reg) begin
            if (!z_reg[19]) begin
                x_reg <= x_reg - y_shift;
                y_reg <= y_reg + x_shift;
                z_reg <= z_reg - atan_val;
            end else begin
                x_reg <= x_reg + y_shift;
                y_reg <= y_reg - x_shift;
                z_reg <= z_reg + atan_val;
            end

            i_reg <= i_reg + 4'd1;
            if (i_reg == 4'd15) begin
                busy_reg <= 1'b0;
                out_valid_reg <= 1'b1;
            end
        end else if (out_valid_reg) begin
            if (out_ready)
                out_valid_reg <= 1'b0;
        end else if (in_valid) begin
            x_reg <= x0;
            y_reg <= 18'd0;
            z_reg <= z0;
            i_reg <= 4'd0;
            busy_reg <= 1'b1;
        end
    end

endmodule
`timescale 1ns/1ps
// @latency 0
module cordic_out (
    input  wire [17:0] x_in,
    input  wire [17:0] y_in,
    output wire [15:0] cos_out,
    output wire [15:0] sin_out
);

    wire signed [18:0] x_extended = {x_in[17], x_in};
    wire signed [18:0] y_extended = {y_in[17], y_in};
    wire signed [18:0] x_rounded = x_extended + 19'sd2;
    wire signed [18:0] y_rounded = y_extended + 19'sd2;

    assign cos_out = x_rounded >>> 2;
    assign sin_out = y_rounded >>> 2;

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
