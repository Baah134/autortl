module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output reg  [255:0] q
);

    wire [255:0] next_q;
    genvar row, col;

    generate
        for (row = 0; row < 16; row = row + 1) begin : gen_row
            for (col = 0; col < 16; col = col + 1) begin : gen_col
                localparam integer ROW_ABOVE = (row + 15) % 16;
                localparam integer ROW_BELOW = (row + 1) % 16;
                localparam integer COL_LEFT  = (col + 15) % 16;
                localparam integer COL_RIGHT = (col + 1) % 16;
                localparam integer CELL = 16 * row + col;

                wire [3:0] neighbors;

                assign neighbors =
                    {3'b000, q[16 * ROW_ABOVE + COL_LEFT]}  +
                    {3'b000, q[16 * ROW_ABOVE + col]}       +
                    {3'b000, q[16 * ROW_ABOVE + COL_RIGHT]} +
                    {3'b000, q[16 * row       + COL_LEFT]}  +
                    {3'b000, q[16 * row       + COL_RIGHT]} +
                    {3'b000, q[16 * ROW_BELOW + COL_LEFT]}  +
                    {3'b000, q[16 * ROW_BELOW + col]}       +
                    {3'b000, q[16 * ROW_BELOW + COL_RIGHT]};

                assign next_q[CELL] = (neighbors == 4'd3) ||
                                      ((neighbors == 4'd2) && q[CELL]);
            end
        end
    endgenerate

    always @(posedge clk) begin
        if (load)
            q <= data;
        else
            q <= next_q;
    end

endmodule
