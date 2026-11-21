`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output wire [255:0] q
);

    reg [255:0] state;
    wire [255:0] next_state;

    (* keep = "true" *) wire [255:0] vertical_parity;
    (* keep = "true" *) wire [255:0] vertical_majority;

    assign q = state;

    function [63:0] neighbor_table;
        input integer target;
        integer index;
        integer total;
        begin
            for (index = 0; index < 64; index = index + 1) begin
                total = {30'b0, index[5:4]} + {30'b0, index[3:2]}
                      + {31'b0, index[1]} + {31'b0, index[0]};
                neighbor_table[index] = (total == target);
            end
        end
    endfunction

    localparam [63:0] TOTAL_TWO   = neighbor_table(2);
    localparam [63:0] TOTAL_THREE = neighbor_table(3);

    genvar row, col;
    generate
        for (row = 0; row < 16; row = row + 1) begin : gen_row
            for (col = 0; col < 16; col = col + 1) begin : gen_col
                localparam integer CENTER = 16 * row + col;
                localparam integer ABOVE  = 16 * ((row + 15) % 16) + col;
                localparam integer BELOW  = 16 * ((row + 1) % 16) + col;
                localparam integer LEFT   = 16 * row + ((col + 15) % 16);
                localparam integer RIGHT  = 16 * row + ((col + 1) % 16);

                wire [5:0] neighbor_index;
                (* keep = "true" *) wire exactly_two;
                (* keep = "true" *) wire exactly_three;

                assign vertical_parity[CENTER] =
                    state[ABOVE] ^ state[CENTER] ^ state[BELOW];
                assign vertical_majority[CENTER] =
                    (state[ABOVE] & state[CENTER]) |
                    (state[ABOVE] & state[BELOW]) |
                    (state[CENTER] & state[BELOW]);

                assign neighbor_index = {
                    vertical_majority[LEFT], vertical_parity[LEFT],
                    vertical_majority[RIGHT], vertical_parity[RIGHT],
                    state[ABOVE], state[BELOW]
                };

                assign exactly_two   = TOTAL_TWO[neighbor_index];
                assign exactly_three = TOTAL_THREE[neighbor_index];
                assign next_state[CENTER] = load ? data[CENTER] :
                    (exactly_three | (state[CENTER] & exactly_two));
            end
        end
    endgenerate

    always @(posedge clk) begin
        state <= next_state;
    end

endmodule