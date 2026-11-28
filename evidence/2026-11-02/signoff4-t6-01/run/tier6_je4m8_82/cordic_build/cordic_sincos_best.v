`timescale 1ns/1ps
// @latency 0
module cordic_prerot (
    input  wire [15:0] angle,
    output wire [17:0] x0,
    output wire [19:0] z0
);

wire [1:0] quadrant;
wire       flip;
wire [15:0] reduced_angle;

assign quadrant      = angle[15:14];
assign flip           = (quadrant == 2'b01) || (quadrant == 2'b10);
assign reduced_angle  = flip ? (angle ^ 16'h8000) : angle;
assign x0             = flip ? 18'd222347 : 18'd39797;
assign z0             = {reduced_angle, 4'b0000};

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
            default: atan_value = 20'd0;
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
    output wire [17:0] y,
    output wire [15:0] cos_out,
    output wire [15:0] sin_out
);

reg busy;
reg in_ready_reg;
reg out_valid_reg;
reg [3:0] i;
reg signed [17:0] x_state;
reg signed [17:0] y_state;
reg [19:0] z_state;
reg [15:0] cos_state;
reg [15:0] sin_state;
wire signed [17:0] x_shift;
wire signed [17:0] y_shift;
wire signed [17:0] x_next;
wire signed [17:0] y_next;
wire signed [18:0] x_next_ext;
wire signed [18:0] y_next_ext;
wire signed [18:0] x_next_rounded;
wire signed [18:0] y_next_rounded;
wire signed [18:0] x0_ext;
wire signed [18:0] x0_rounded;

assign x_shift = x_state >>> i;
assign y_shift = y_state >>> i;

assign x_next = !z_state[19] ? (x_state - y_shift) : (x_state + y_shift);
assign y_next = !z_state[19] ? (y_state + x_shift) : (y_state - x_shift);

assign x_next_ext = {{1{x_next[17]}}, x_next};
assign y_next_ext = {{1{y_next[17]}}, y_next};
assign x_next_rounded = x_next_ext + 19'sd2;
assign y_next_rounded = y_next_ext + 19'sd2;

assign x0_ext = {{3{x0[17]}}, x0};
assign x0_rounded = x0_ext + 19'sd2;

assign in_ready = in_ready_reg;
assign out_valid = out_valid_reg;
assign iter = i;
assign x = x_state;
assign y = y_state;
assign cos_out = cos_state;
assign sin_out = sin_state;

always @(posedge clk) begin
    if (rst) begin
        busy <= 1'b0;
        in_ready_reg <= 1'b1;
        out_valid_reg <= 1'b0;
        i <= 4'd0;
        x_state <= 18'd0;
        y_state <= 18'd0;
        z_state <= 20'd0;
        cos_state <= 16'd0;
        sin_state <= 16'd0;
    end else if (busy) begin
        x_state <= x_next;
        y_state <= y_next;
        if (!z_state[19])
            z_state <= z_state - atan_val;
        else
            z_state <= z_state + atan_val;

        cos_state <= x_next_rounded[17:2];
        sin_state <= y_next_rounded[17:2];

        i <= i + 4'd1;
        in_ready_reg <= 1'b0;
        if (i == 4'd15) begin
            busy <= 1'b0;
            out_valid_reg <= 1'b1;
        end
    end else if (out_valid_reg) begin
        if (out_ready) begin
            out_valid_reg <= 1'b0;
            in_ready_reg <= 1'b1;
        end else begin
            in_ready_reg <= 1'b0;
        end
    end else if (in_valid) begin
        x_state <= x0;
        y_state <= 18'd0;
        z_state <= z0;
        i <= 4'd0;
        busy <= 1'b1;
        in_ready_reg <= 1'b0;
        cos_state <= x0_rounded[17:2];
        sin_state <= 16'd0;
    end else begin
        in_ready_reg <= 1'b1;
    end
end

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
        .y(w_cordic_engine_y),
        .cos_out(cos_out),
        .sin_out(sin_out)
    );

endmodule