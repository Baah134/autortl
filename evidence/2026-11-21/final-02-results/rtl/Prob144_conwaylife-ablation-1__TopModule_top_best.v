`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input wire clk,
    input wire load,
    input wire [255:0] data,
    output wire [255:0] q
);
    // The paired tables use the lower half for O5 and the upper half
    // for O6 with I5 high. Physical LUT packing is left to Vivado.
    localparam [63:0] HORIZONTAL_TABLE = 64'hE8E8E8E8_96969696;
    localparam [63:0] SUBTOTAL_LOW_TABLE = 64'h936C936C_5A5A5A5A;
    localparam [15:0] SUBTOTAL_HIGH_TABLE = 16'hEC80;

    // Each byte covers subtotal 0 through 7 for one center/side pattern.
    // With k live side neighbors, the only set bits are at 3-k and,
    // for a live center, 2-k. Subtotals 4 through 7 always give zero.
    localparam [63:0] LIFE_TABLE = 64'h0306060C_02040408;

    reg [255:0] state;
    wire [255:0] evolved;
    (* keep = "true" *) wire [255:0] horizontal_parity;
    (* keep = "true" *) wire [255:0] horizontal_majority;

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

                wire [2:0] horizontal_inputs;
                wire [3:0] subtotal_inputs;
                (* keep = "true" *) wire [2:0] subtotal;
                wire [5:0] life_inputs;

                assign horizontal_inputs = {state[RIGHT], state[CELL], state[LEFT]};
                assign horizontal_parity[CELL] =
                    HORIZONTAL_TABLE[{3'b000, horizontal_inputs}];
                assign horizontal_majority[CELL] =
                    HORIZONTAL_TABLE[{3'b100, horizontal_inputs}];

                assign subtotal_inputs = {
                    horizontal_majority[BELOW], horizontal_parity[BELOW],
                    horizontal_majority[ABOVE], horizontal_parity[ABOVE]
                };
                assign subtotal[0] = SUBTOTAL_LOW_TABLE[{2'b00, subtotal_inputs}];
                assign subtotal[1] = SUBTOTAL_LOW_TABLE[{2'b10, subtotal_inputs}];
                assign subtotal[2] = SUBTOTAL_HIGH_TABLE[subtotal_inputs];

                assign life_inputs = {state[CELL], state[RIGHT], state[LEFT], subtotal};
                assign evolved[CELL] = LIFE_TABLE[life_inputs];
            end
        end
    endgenerate

    // The two triplet counts plus the two side bits cover all eight
    // neighbors for every one of the 512 binary local patterns.
    // The corner block uses bits 0, 15, 240 and 255. The seeded blinker
    // alternates between bits 0, 16, 32 and bits 16, 17, 31.
    always @(posedge clk) begin
        if (load)
            state <= data;
        else
            state <= evolved;
    end
endmodule