`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output wire [255:0] q
);

    reg  [255:0] state;
    wire [255:0] vertical_low;
    wire [255:0] vertical_high;
    wire [255:0] next_state;

    assign q = state;

    // Each rule table uses two two-bit counts and two single-bit neighbors.
    function [63:0] make_rule_table;
        input alive;
        integer index;
        integer count;
        begin
            for (index = 0; index < 64; index = index + 1) begin
                count = {30'b0, index[5:4]} + {30'b0, index[3:2]}
                      + {31'b0, index[1]} + {31'b0, index[0]};
                make_rule_table[index] = (count == 3) ||
                                         (alive && (count == 2));
            end
        end
    endfunction

    localparam [63:0] BIRTH_TABLE   = make_rule_table(1'b0);
    localparam [63:0] SURVIVE_TABLE = make_rule_table(1'b1);

    genvar row, col;
    generate
        for (row = 0; row < 16; row = row + 1) begin : grid_row
            for (col = 0; col < 16; col = col + 1) begin : grid_col
                localparam integer CELL  = 16 * row + col;
                localparam integer ABOVE = 16 * ((row + 15) % 16) + col;
                localparam integer BELOW = 16 * ((row + 1) % 16) + col;
                localparam integer LEFT  = 16 * row + ((col + 15) % 16);
                localparam integer RIGHT = 16 * row + ((col + 1) % 16);

                wire [5:0] rule_index;

                // Both adjacent columns reuse this parity and majority pair.
                assign vertical_low[CELL] = state[ABOVE] ^ state[CELL] ^
                                            state[BELOW];
                assign vertical_high[CELL] = (state[ABOVE] & state[CELL]) |
                                             (state[ABOVE] & state[BELOW]) |
                                             (state[CELL] & state[BELOW]);

                assign rule_index = {vertical_high[LEFT], vertical_low[LEFT],
                                     vertical_high[RIGHT], vertical_low[RIGHT],
                                     state[ABOVE], state[BELOW]};
                assign next_state[CELL] = state[CELL] ?
                                          SURVIVE_TABLE[rule_index] :
                                          BIRTH_TABLE[rule_index];
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