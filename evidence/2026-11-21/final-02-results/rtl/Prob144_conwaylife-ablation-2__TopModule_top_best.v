`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input wire clk,
    input wire load,
    input wire [255:0] data,
    output wire [255:0] q
);

    function [63:0] population_table;
        input integer lower;
        input integer upper;
        integer address;
        integer population;
        begin
            for (address = 0; address < 64; address = address + 1) begin
                population = {2'b00, address[5:4]} +
                             {2'b00, address[3:2]} +
                             {2'b00, address[1:0]};
                population_table[address] =
                    (population >= lower) && (population <= upper);
            end
        end
    endfunction

    localparam [63:0] POPULATION_THREE_OR_FOUR = population_table(3, 4);

    reg [255:0] board;
    assign q = board;

    genvar row, col, pair_index;
    generate
        for (row = 0; row < 16; row = row + 1) begin : gen_row
            localparam integer ROW_BASE = 16 * row;
            localparam integer ABOVE_BASE = 16 * ((row + 15) % 16);
            localparam integer BELOW_BASE = 16 * ((row + 1) % 16);

            wire [15:0] count_low;
            wire [15:0] count_high;
            (* keep = "true" *) wire [7:0] pair_parity;

            for (pair_index = 0; pair_index < 8; pair_index = pair_index + 1) begin : gen_pair
                assign pair_parity[pair_index] =
                    count_low[2 * pair_index] ^ count_low[2 * pair_index + 1];
            end

            for (col = 0; col < 16; col = col + 1) begin : gen_col
                localparam integer CELL = ROW_BASE + col;
                localparam integer LEFT = (col + 15) % 16;
                localparam integer RIGHT = (col + 1) % 16;
                localparam integer REMAINING = (col % 2 == 0) ? LEFT : RIGHT;

                wire above_alive;
                wire center_alive;
                wire below_alive;
                wire [5:0] counts;
                (* keep = "true" *) wire population_matches;

                assign above_alive = board[ABOVE_BASE + col];
                assign center_alive = board[CELL];
                assign below_alive = board[BELOW_BASE + col];

                // Parity and majority share the same three inputs for LUT packing.
                assign count_low[col] = above_alive ^ center_alive ^ below_alive;
                assign count_high[col] = (above_alive & center_alive) |
                                         (above_alive & below_alive) |
                                         (center_alive & below_alive);

                assign counts = {count_high[LEFT], count_low[LEFT],
                                 count_high[col], count_low[col],
                                 count_high[RIGHT], count_low[RIGHT]};
                assign population_matches = POPULATION_THREE_OR_FOUR[counts];

                // Among populations three and four, only three has odd parity.
                always @(posedge clk) begin
                    if (load)
                        board[CELL] <= data[CELL];
                    else
                        board[CELL] <= population_matches &
                            ((pair_parity[col / 2] ^ count_low[REMAINING]) |
                             center_alive);
                end
            end
        end
    endgenerate
endmodule