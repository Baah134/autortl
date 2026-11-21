`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input wire clk,
    input wire resetn,
    input wire x,
    input wire y,
    output wire f,
    output wire g
);
    localparam [2:0] START    = 3'b000;
    localparam [2:0] F_PULSE  = 3'b100;
    localparam [2:0] EMPTY    = 3'b001;
    localparam [2:0] MATCH_1  = 3'b010;
    localparam [2:0] MATCH_10 = 3'b011;
    localparam [2:0] FAILURE  = 3'b101;

    localparam [2:0] Y_FIRST  = EMPTY;
    localparam [2:0] Y_SECOND = MATCH_1;
    localparam [2:0] SUCCESS  = MATCH_10;

    reg [2:0] control;
    reg f_state;
    reg g_state;

    wire [2:0] next_control;
    wire next_f;
    wire next_g;

    assign f = f_state;
    assign g = g_state;

    assign next_f = !g_state && (control == START);

    // With g high, only the second y sample can clear g.
    assign next_g =
        (!g_state && (control == MATCH_10) && x) ||
        (g_state && ((control == Y_FIRST) || (control == SUCCESS) ||
                     ((control == Y_SECOND) && y)));

    assign next_control[2] =
        (!g_state && ((control == START) || (control == FAILURE))) ||
        (g_state && (control == Y_SECOND) && !y);

    assign next_control[1] =
        (!g_state && (((control == EMPTY) && x) || (control == MATCH_1))) ||
        (g_state && ((control == Y_FIRST) || (control == SUCCESS) ||
                     ((control == Y_SECOND) && y)));

    // Both outcomes of the second y sample have bit 0 set.
    assign next_control[0] =
        (!g_state && ((control == F_PULSE) || (control == MATCH_10) ||
                      (control == FAILURE) ||
                      (!x && ((control == EMPTY) || (control == MATCH_1))))) ||
        (g_state && ((control == Y_SECOND) || (control == SUCCESS) ||
                     ((control == Y_FIRST) && y)));

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