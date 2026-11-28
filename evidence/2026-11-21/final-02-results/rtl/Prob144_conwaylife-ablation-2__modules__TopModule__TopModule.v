`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output wire [255:0] q
);

    function [63:0] population_table;
        input integer target;
        integer address;
        integer population;
        begin
            for (address = 0; address < 64; address = address + 1) begin
                population = address[5:4] + address[3:2] + address[1:0];
                population_table[address] = (population == target);
            end
        end
    endfunction

    localparam [63:0] POPULATION_THREE = population_table(3);
    localparam [63:0] POPULATION_FOUR  = population_table(4);

    reg  [255:0] board;
    wire [511:0] vertical_count;

    assign q = board;

    genvar row, col;
    generate
        for (row = 0; row < 16; row = row + 1) begin : gen_row
            for (col = 0; col < 16; col = col + 1) begin : gen_col
                localparam integer CELL = 16 * row + col;
                localparam integer ABOVE = 16 * ((row + 15) % 16) + col;
                localparam integer BELOW = 16 * ((row + 1) % 16) + col;
                localparam integer LEFT  = 16 * row + ((col + 15) % 16);
                localparam integer RIGHT = 16 * row + ((col + 1) % 16);

                wire above_alive, center_alive, below_alive;
                wire [5:0] counts;
                wire exactly_three, exactly_four;
                wire next_alive;

                assign above_alive  = board[ABOVE];
                assign center_alive = board[CELL];
                assign below_alive  = board[BELOW];

                assign vertical_count[2*CELL] =
                    above_alive ^ center_alive ^ below_alive;
                assign vertical_count[2*CELL+1] =
                    (above_alive & center_alive) |
                    (above_alive & below_alive) |
                    (center_alive & below_alive);

                assign counts = {vertical_count[2*LEFT  +: 2],
                                 vertical_count[2*CELL  +: 2],
                                 vertical_count[2*RIGHT +: 2]};
                assign exactly_three = POPULATION_THREE[counts];
                assign exactly_four  = POPULATION_FOUR[counts];
                assign next_alive = exactly_three | (exactly_four & center_alive);

                always @(posedge clk) begin
                    if (load)
                        board[CELL] <= data[CELL];
                    else
                        board[CELL] <= next_alive;
                end
            end
        end
    endgenerate
endmodule