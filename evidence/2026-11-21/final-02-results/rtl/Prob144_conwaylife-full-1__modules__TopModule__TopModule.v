`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output wire [255:0] q
);

    reg  [255:0] state;
    wire [255:0] window_low;
    wire [255:0] window_high;
    wire [255:0] next_state;

    // Each table is indexed by {above_count, middle_count, below_count}.
    // The three windows include the center cell in their combined count.
    localparam [63:0] DEAD_CENTER_RULE = 64'h0001_0012_0124_1248;
    localparam [63:0] LIVE_CENTER_RULE = 64'h0013_0136_136C_36C8;

    assign q = state;

    genvar row, col;
    generate
        for (row = 0; row < 16; row = row + 1) begin : gen_row
            for (col = 0; col < 16; col = col + 1) begin : gen_col
                localparam integer CELL  = 16 * row + col;
                localparam integer LEFT  = 16 * row + ((col + 15) % 16);
                localparam integer RIGHT = 16 * row + ((col + 1) % 16);
                localparam integer ABOVE = 16 * ((row + 15) % 16) + col;
                localparam integer BELOW = 16 * ((row + 1) % 16) + col;

                wire [5:0] count_index;

                // Parity and majority encode the population of each window.
                assign window_low[CELL] =
                    state[LEFT] ^ state[CELL] ^ state[RIGHT];
                assign window_high[CELL] =
                    (state[LEFT] & state[CELL]) |
                    (state[LEFT] & state[RIGHT]) |
                    (state[CELL] & state[RIGHT]);

                assign count_index = {
                    window_high[ABOVE], window_low[ABOVE],
                    window_high[CELL],  window_low[CELL],
                    window_high[BELOW], window_low[BELOW]
                };

                assign next_state[CELL] = state[CELL]
                    ? LIVE_CENTER_RULE[count_index]
                    : DEAD_CENTER_RULE[count_index];
            end
        end
    endgenerate

    always @(posedge clk) begin
        if (load)
            state <= data;
        else
            state <= next_state;
    end

endmodule