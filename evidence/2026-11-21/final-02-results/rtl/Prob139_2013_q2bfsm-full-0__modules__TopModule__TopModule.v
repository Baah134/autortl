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
    reg matching;
    reg phase;
    reg tail;

    wire reset_state;
    wire sample_x;
    wire detected;
    wire keep_g;

    assign f = f_state;
    assign g = g_state;

    // State encoding             f  g  matching  phase  tail
    // A                          0  0      0       0     0
    // Startup pulse              1  0      0       0     0
    // No matched prefix          0  0      1       0     0
    // Matched 1                  0  0      1       1     0
    // Matched 10                 0  0      1       0     1
    // Await first y sample       0  1      0       0     0
    // Await second y sample      0  1      0       1     0
    // Hold g high                0  1      0       0     1
    // Hold g low                 0  0      0       0     1

    assign reset_state = ~(f_state | g_state | matching | phase | tail);
    assign sample_x = f_state | matching;
    assign detected = matching & tail & x;
    assign keep_g = tail | y;

    always @(posedge clk) begin
        if (!resetn) begin
            f_state  <= 1'b0;
            g_state  <= 1'b0;
            matching <= 1'b0;
            phase    <= 1'b0;
            tail     <= 1'b0;
        end else begin
            f_state  <= reset_state;
            g_state  <= detected | (g_state & (keep_g | ~phase));
            matching <= sample_x & ~detected;
            phase    <= (sample_x & x & ~tail)
                      | (g_state & ~phase & ~keep_g);
            tail     <= (matching & phase & ~x)
                      | (g_state & (y | phase))
                      | (~matching & tail);
        end
    end

endmodule