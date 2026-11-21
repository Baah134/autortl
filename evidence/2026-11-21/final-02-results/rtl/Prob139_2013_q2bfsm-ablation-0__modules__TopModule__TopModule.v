`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire resetn,
    input  wire x,
    input  wire y,
    output wire f,
    output wire g
);

    localparam [2:0] START       = 3'b000;
    localparam [2:0] EMPTY_OR_Y1 = 3'b001;
    localparam [2:0] PREFIX_1    = 3'b010;
    localparam [2:0] PREFIX_10   = 3'b011;
    localparam [2:0] Y2_FIRST_0  = 3'b100;
    localparam [2:0] Y2_FIRST_1  = 3'b101;
    localparam [2:0] DONE        = 3'b110;

    (* fsm_encoding = "none" *) reg [2:0] phase;
    reg f_reg;
    reg g_reg;

    reg [2:0] next_phase;
    reg next_f;
    reg next_g;

    assign f = f_reg;
    assign g = g_reg;

    always @(*) begin
        next_phase = phase;
        next_f = 1'b0;
        next_g = g_reg;

        case (phase)
            START: begin
                // f distinguishes state A from the pulse cycle.
                if (f_reg)
                    next_phase = x ? PREFIX_1 : EMPTY_OR_Y1;
                else
                    next_f = 1'b1;
            end

            EMPTY_OR_Y1: begin
                // g distinguishes the empty prefix from the first y sample.
                if (g_reg)
                    next_phase = y ? Y2_FIRST_1 : Y2_FIRST_0;
                else if (x)
                    next_phase = PREFIX_1;
            end

            PREFIX_1: begin
                if (!x)
                    next_phase = PREFIX_10;
            end

            PREFIX_10: begin
                next_phase = EMPTY_OR_Y1;
                next_g = x;
            end

            Y2_FIRST_0: begin
                next_phase = DONE;
                next_g = y;
            end

            Y2_FIRST_1: begin
                next_phase = DONE;
                next_g = 1'b1;
            end

            DONE: begin
                next_phase = DONE;
            end

            default: begin
                next_phase = START;
                next_g = 1'b0;
            end
        endcase
    end

    always @(posedge clk) begin
        if (!resetn) begin
            phase <= START;
            f_reg <= 1'b0;
            g_reg <= 1'b0;
        end else begin
            phase <= next_phase;
            f_reg <= next_f;
            g_reg <= next_g;
        end
    end

endmodule