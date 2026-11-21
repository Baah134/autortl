`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output wire [255:0] q
);

    reg [255:0] state;
    wire [1:0] horizontal_count [0:255];

    assign q = state;

    genvar row, col;
    generate
        for (row = 0; row < 16; row = row + 1) begin : gen_row
            for (col = 0; col < 16; col = col + 1) begin : gen_col
                localparam integer CENTER = 16 * row + col;
                localparam integer LEFT   = 16 * row + ((col + 15) % 16);
                localparam integer RIGHT  = 16 * row + ((col + 1) % 16);
                localparam integer ABOVE  = 16 * ((row + 15) % 16) + col;
                localparam integer BELOW  = 16 * ((row + 1) % 16) + col;

                wire left_alive;
                wire right_alive;
                wire center_alive;
                wire [1:0] side_count;
                wire [5:0] neighbor_counts;
                reg count_is_two;
                reg count_is_three;

                assign left_alive   = state[LEFT];
                assign right_alive  = state[RIGHT];
                assign center_alive = state[CENTER];

                // The cells above and below both use this three-cell count.
                assign horizontal_count[CENTER][0] =
                    left_alive ^ center_alive ^ right_alive;
                assign horizontal_count[CENTER][1] =
                    (left_alive & center_alive) |
                    (left_alive & right_alive) |
                    (center_alive & right_alive);

                assign side_count[0] = left_alive ^ right_alive;
                assign side_count[1] = left_alive & right_alive;

                assign neighbor_counts = {
                    horizontal_count[ABOVE], side_count, horizontal_count[BELOW]
                };

                // Decode the three partial counts directly from their six bits.
                always @(*) begin
                    count_is_two   = 1'b0;
                    count_is_three = 1'b0;
                    case (neighbor_counts)
                        6'b10_00_00, 6'b00_10_00, 6'b00_00_10,
                        6'b01_01_00, 6'b01_00_01, 6'b00_01_01:
                            count_is_two = 1'b1;

                        6'b11_00_00, 6'b00_00_11,
                        6'b10_01_00, 6'b10_00_01, 6'b01_10_00,
                        6'b00_10_01, 6'b01_00_10, 6'b00_01_10,
                        6'b01_01_01:
                            count_is_three = 1'b1;

                        default: begin
                            count_is_two   = 1'b0;
                            count_is_three = 1'b0;
                        end
                    endcase
                end

                always @(posedge clk) begin
                    if (load)
                        state[CENTER] <= data[CENTER];
                    else
                        state[CENTER] <= count_is_three |
                                         (count_is_two & center_alive);
                end
            end
        end
    endgenerate

endmodule