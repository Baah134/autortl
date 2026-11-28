module TopModule (
    input clk,
    input load,
    input [255:0] data,
    output reg [255:0] q
);

    wire [255:0] q_next;

    genvar r, c;
    generate
        for (r = 0; r < 16; r = r + 1) begin : gen_row
            for (c = 0; c < 16; c = c + 1) begin : gen_col
                localparam r_up    = (r == 0)  ? 15 : (r - 1);
                localparam r_down  = (r == 15) ? 0  : (r + 1);
                localparam c_left  = (c == 0)  ? 15 : (c - 1);
                localparam c_right = (c == 15) ? 0  : (c + 1);

                wire [3:0] neighbors = q[r_up * 16 + c_left]
                                     + q[r_up * 16 + c]
                                     + q[r_up * 16 + c_right]
                                     + q[r * 16 + c_left]
                                     + q[r * 16 + c_right]
                                     + q[r_down * 16 + c_left]
                                     + q[r_down * 16 + c]
                                     + q[r_down * 16 + c_right];

                assign q_next[r * 16 + c] = (neighbors == 4'd3) ? 1'b1 :
                                            (neighbors == 4'd2) ? q[r * 16 + c] :
                                                                  1'b0;
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
