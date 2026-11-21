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

    localparam [2:0] A          = 3'd0;
    localparam [2:0] SEARCH    = 3'd1;
    localparam [2:0] PREFIX_1  = 3'd2;
    localparam [2:0] PREFIX_10 = 3'd3;
    localparam [2:0] SAMPLE_Y1 = 3'd4;
    localparam [2:0] SAMPLE_Y2 = 3'd5;
    localparam [2:0] HOLD      = 3'd6;

    (* fsm_encoding = "none" *) reg [2:0] state;
    reg [2:0] next_state;
    reg f_reg, g_reg;
    reg next_f, next_g;

    assign f = f_reg;
    assign g = g_reg;

    always @(*) begin
        next_state = state;
        next_f = 1'b0;
        next_g = g_reg;

        case (state)
            A: begin
                next_state = SEARCH;
                next_f = 1'b1;
            end
            SEARCH: begin
                if (x)
                    next_state = PREFIX_1;
            end
            PREFIX_1: begin
                if (!x)
                    next_state = PREFIX_10;
            end
            PREFIX_10: begin
                if (x) begin
                    next_state = SAMPLE_Y1;
                    next_g = 1'b1;
                end else begin
                    next_state = SEARCH;
                end
            end
            SAMPLE_Y1: begin
                if (y)
                    next_state = HOLD;
                else
                    next_state = SAMPLE_Y2;
            end
            SAMPLE_Y2: begin
                next_state = HOLD;
                next_g = y;
            end
            HOLD: begin
                next_state = HOLD;
            end
            default: begin
                next_state = A;
                next_g = 1'b0;
            end
        endcase
    end

    always @(posedge clk) begin
        if (!resetn) begin
            state <= A;
            f_reg <= 1'b0;
            g_reg <= 1'b0;
        end else begin
            state <= next_state;
            f_reg <= next_f;
            g_reg <= next_g;
        end
    end

endmodule