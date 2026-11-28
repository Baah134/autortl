module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output reg  [255:0] q
);

    reg [255:0] q_next;

    integer r, c;
    integer r_up, r_down, c_left, c_right;
    integer count;

    always @(*) begin
        for (r = 0; r < 16; r = r + 1) begin
            for (c = 0; c < 16; c = c + 1) begin
                r_up    = (r == 15) ? 0 : (r + 1);
                r_down  = (r == 0)  ? 15 : (r - 1);
                c_right = (c == 15) ? 0 : (c + 1);
                c_left  = (c == 0)  ? 15 : (c - 1);

                count = q[r_down  * 16 + c_left]  +
                        q[r_down  * 16 + c]       +
                        q[r_down  * 16 + c_right] +
                        q[r       * 16 + c_left]  +
                        q[r       * 16 + c_right] +
                        q[r_up    * 16 + c_left]  +
                        q[r_up    * 16 + c]       +
                        q[r_up    * 16 + c_right];

                case (count)
                    2:       q_next[r * 16 + c] = q[r * 16 + c];
                    3:       q_next[r * 16 + c] = 1'b1;
                    default: q_next[r * 16 + c] = 1'b0;
                endcase
            end
        end
    end

    always @(posedge clk) begin
        if (load) begin
            q <= data;
        end else begin
            q <= q_next;
        end
    end

endmodule
