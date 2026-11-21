`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output wire [255:0] q
);

    reg  [255:0] state;
    wire [255:0] evolved;
    wire [1:0] horizontal_count [0:255];

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

                wire left_alive;
                wire cell_alive;
                wire right_alive;
                wire [2:0] subtotal;

                assign left_alive  = state[LEFT];
                assign cell_alive  = state[CELL];
                assign right_alive = state[RIGHT];

                assign horizontal_count[CELL][0] =
                    left_alive ^ cell_alive ^ right_alive;
                assign horizontal_count[CELL][1] =
                    (left_alive & cell_alive) |
                    (left_alive & right_alive) |
                    (cell_alive & right_alive);

                assign subtotal = {1'b0, horizontal_count[ABOVE]} +
                                  {1'b0, horizontal_count[BELOW]};

                // Three neighbors yield a live cell. Two preserve its state.
                assign evolved[CELL] =
                    ((subtotal == 3'd0) &
                        cell_alive & left_alive & right_alive) |
                    ((subtotal == 3'd1) &
                        ((left_alive & right_alive) |
                         (cell_alive & (left_alive ^ right_alive)))) |
                    ((subtotal == 3'd2) &
                        ((left_alive ^ right_alive) |
                         (cell_alive & ~left_alive & ~right_alive))) |
                    ((subtotal == 3'd3) & ~left_alive & ~right_alive);
            end
        end
    endgenerate

    always @(posedge clk) begin
        if (load)
            state <= data;
        else
            state <= evolved;
    end

endmodule