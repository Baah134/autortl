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

    localparam [2:0] START      = 3'b000;
    localparam [2:0] EMPTY      = 3'b001;
    localparam [2:0] MATCH_1    = 3'b010;
    localparam [2:0] MATCH_10   = 3'b011;
    localparam [2:0] FAILURE    = 3'b100;

    // The registered g bit selects the interpretation of these codes.
    localparam [2:0] Y_FIRST    = EMPTY;
    localparam [2:0] Y_SECOND   = MATCH_1;
    localparam [2:0] SUCCESS    = MATCH_10;

    reg [2:0] control;
    reg [2:0] next_control;
    reg f_state, g_state;
    reg next_f, next_g;

    assign f = f_state;
    assign g = g_state;

    always @(*) begin
        next_control = EMPTY;
        next_f = 1'b0;
        next_g = 1'b0;

        if (g_state) begin
            case (control)
                Y_FIRST: begin
                    next_control = y ? SUCCESS : Y_SECOND;
                    next_g = 1'b1;
                end
                Y_SECOND: begin
                    next_control = y ? SUCCESS : FAILURE;
                    next_g = y;
                end
                SUCCESS: begin
                    next_control = SUCCESS;
                    next_g = 1'b1;
                end
                default: next_control = FAILURE;
            endcase
        end else if (f_state) begin
            next_control = EMPTY;
        end else begin
            case (control)
                START: begin
                    next_control = START;
                    next_f = 1'b1;
                end
                EMPTY: next_control = x ? MATCH_1 : EMPTY;
                MATCH_1: next_control = x ? MATCH_1 : MATCH_10;
                MATCH_10: begin
                    next_control = x ? Y_FIRST : EMPTY;
                    next_g = x;
                end
                FAILURE: next_control = FAILURE;
                default: next_control = FAILURE;
            endcase
        end
    end

    always @(posedge clk) begin
        if (!resetn) begin
            control <= START;
            f_state <= 1'b0;
            g_state <= 1'b0;
        end else begin
            control <= next_control;
            f_state <= next_f;
            g_state <= next_g;
        end
    end

endmodule