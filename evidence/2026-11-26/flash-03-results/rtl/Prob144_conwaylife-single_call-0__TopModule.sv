module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output reg  [255:0] q
);

    wire [255:0] q_next;

    genvar r, c;
    generate
        for (r = 0; r < 16; r = r + 1) begin : gen_rows
            for (c = 0; c < 16; c = c + 1) begin : gen_cols
                localparam integer r_up   = (r == 15) ? 0  : (r + 1);
                localparam integer r_down = (r == 0)  ? 15 : (r - 1);
                localparam integer c_rgt  = (c == 15) ? 0  : (c + 1);
                localparam integer c_lft  = (c == 0)  ? 15 : (c - 1);

                wire [3:0] neighbors;
                assign neighbors = q[r_up   * 16 + c_lft] +
                                   q[r_up   * 16 + c]     +
                                   q[r_up   * 16 + c_rgt] +
                                   q[r      * 16 + c_lft] +
                                   q[r      * 16 + c_rgt] +
                                   q[r_down * 16 + c_lft] +
                                   q[r_down * 16 + c]     +
                                   q[r_down * 16 + c_rgt];

                assign q_next[r * 16 + c] = (neighbors == 4'd2) ? q[r * 16 + c] :
                                            (neighbors == 4'd3) ? 1'b1 : 1'b0;
            end
        end
    endgenerate

    always @(posedge clk) begin
        if (load) begin
            q <= data;
        end else begin
            q <= q_next;
        end
    end

endmodule
