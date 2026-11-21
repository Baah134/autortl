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

    reg f_state;
    reg g_state;
    reg terminal;
    reg prefix_hi;
    reg prefix_lo;

    assign f = f_state;
    assign g = g_state;

    // While searching, 01, 11, and 10 encode empty, 1, and 10.
    // With g high and terminal clear, prefix_lo selects the y sample.
    // In a terminal state, g holds the result.
    wire start = !g_state && !terminal && !prefix_hi && !prefix_lo;
    wire search = !g_state && !terminal && (prefix_hi || prefix_lo);
    wire prefix_one = prefix_hi && prefix_lo;
    wire prefix_ten = prefix_hi && !prefix_lo;
    wire match = search && prefix_ten && x;
    wire advance_window = g_state && !terminal && !prefix_lo && !y;

    always @(posedge clk) begin
        if (!resetn) begin
            f_state   <= 1'b0;
            g_state   <= 1'b0;
            terminal  <= 1'b0;
            prefix_hi <= 1'b0;
            prefix_lo <= 1'b0;
        end else begin
            f_state <= start;
            g_state <= match || (g_state && (terminal || y || !prefix_lo));
            terminal <= terminal || (g_state && (y || prefix_lo));
            prefix_hi <= search && ((x && !prefix_ten) ||
                                    (!x && prefix_one));
            prefix_lo <= start || advance_window ||
                         (search && ((x && !prefix_ten) ||
                                     (!x && !prefix_one)));
        end
    end

endmodule