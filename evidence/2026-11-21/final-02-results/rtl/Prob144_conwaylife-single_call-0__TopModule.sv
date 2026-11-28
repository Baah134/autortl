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
            localparam integer ABOVE = (row + 15) % 16;
            localparam integer BELOW = (row + 1) % 16;

            for (col = 0; col < 16; col = col + 1) begin : gen_col
                localparam integer LEFT  = (col + 15) % 16;
                localparam integer RIGHT = (col + 1) % 16;
                localparam integer CELL  = 16 * row + col;

                wire [3:0] neighbors;
                assign neighbors =
                    {3'b000, q[16 * ABOVE + LEFT]}  +
                    {3'b000, q[16 * ABOVE + col]}   +
                    {3'b000, q[16 * ABOVE + RIGHT]} +
                    {3'b000, q[16 * row   + LEFT]}  +
                    {3'b000, q[16 * row   + RIGHT]} +
                    {3'b000, q[16 * BELOW + LEFT]}  +
                    {3'b000, q[16 * BELOW + col]}   +
                    {3'b000, q[16 * BELOW + RIGHT]};

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
