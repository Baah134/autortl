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
                wire [3:0] count;

                assign count = {3'b0, q[((r == 0)  ? 15 : r - 1)  * 16 + ((c == 0)  ? 15 : c - 1)]} +
                               {3'b0, q[((r == 0)  ? 15 : r - 1)  * 16 + c]}                          +
                               {3'b0, q[((r == 0)  ? 15 : r - 1)  * 16 + ((c == 15) ? 0  : c + 1)]} +
                               {3'b0, q[r                         * 16 + ((c == 0)  ? 15 : c - 1)]} +
                               {3'b0, q[r                         * 16 + ((c == 15) ? 0  : c + 1)]} +
                               {3'b0, q[((r == 15) ? 0  : r + 1)  * 16 + ((c == 0)  ? 15 : c - 1)]} +
                               {3'b0, q[((r == 15) ? 0  : r + 1)  * 16 + c]}                          +
                               {3'b0, q[((r == 15) ? 0  : r + 1)  * 16 + ((c == 15) ? 0  : c + 1)]};

                assign q_next[r * 16 + c] = (count == 4'd3) ? 1'b1 :
                                            (count == 4'd2) ? q[r * 16 + c] :
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
