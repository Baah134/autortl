`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output wire [255:0] q
);

    // Candidate verification, routed metrics, and promotion remain pending.
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
                wire [4:0] partial_inputs;
                reg [1:0] partial_code;
                reg next_alive;

                assign left_alive   = state[LEFT];
                assign right_alive  = state[RIGHT];
                assign center_alive = state[CENTER];

                // Both vertically adjacent cells reuse these two count bits.
                assign horizontal_count[CENTER][0] =
                    left_alive ^ center_alive ^ right_alive;
                assign horizontal_count[CENTER][1] =
                    (left_alive & center_alive) |
                    (left_alive & right_alive) |
                    (center_alive & right_alive);

                // Both code bits depend on the same five inputs for LUT packing.
                assign partial_inputs = {
                    horizontal_count[ABOVE],
                    horizontal_count[BELOW],
                    left_alive
                };

                always @(*) begin
                    partial_code = 2'd0;
                    case (partial_inputs)
                        5'b00_01_0, 5'b01_00_0, 5'b00_00_1:
                            partial_code = 2'd1;

                        5'b00_10_0, 5'b01_01_0, 5'b10_00_0,
                        5'b00_01_1, 5'b01_00_1:
                            partial_code = 2'd2;

                        5'b00_11_0, 5'b01_10_0, 5'b10_01_0,
                        5'b11_00_0, 5'b00_10_1, 5'b01_01_1,
                        5'b10_00_1:
                            partial_code = 2'd3;

                        default: partial_code = 2'd0;
                    endcase
                end

                always @(*) begin
                    next_alive = 1'b0;
                    if (load) begin
                        next_alive = data[CENTER];
                    end else begin
                        case (partial_code)
                            2'd1: next_alive = right_alive & center_alive;
                            2'd2: next_alive = right_alive | center_alive;
                            2'd3: next_alive = ~right_alive;
                            default: next_alive = 1'b0;
                        endcase
                    end
                end

                always @(posedge clk) begin
                    state[CENTER] <= next_alive;
                end
            end
        end
    endgenerate

endmodule