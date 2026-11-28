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
            localparam integer ABOVE = ((row + 15) % 16) * 16;
            localparam integer CENTER = row * 16;
            localparam integer BELOW = ((row + 1) % 16) * 16;

            for (col = 0; col < 16; col = col + 1) begin : gen_col
                localparam integer LEFT = (col + 15) % 16;
                localparam integer RIGHT = (col + 1) % 16;

                wire [3:0] neighbors;
                assign neighbors = {3'b000, q[ABOVE  + LEFT]}
                                 + {3'b000, q[ABOVE  + col]}
                                 + {3'b000, q[ABOVE  + RIGHT]}
                                 + {3'b000, q[CENTER + LEFT]}
                                 + {3'b000, q[CENTER + RIGHT]}
                                 + {3'b000, q[BELOW  + LEFT]}
                                 + {3'b000, q[BELOW  + col]}
                                 + {3'b000, q[BELOW  + RIGHT]};

                assign next_q[CENTER + col] = (neighbors == 4'd3)
                                            | ((neighbors == 4'd2) & q[CENTER + col]);
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
