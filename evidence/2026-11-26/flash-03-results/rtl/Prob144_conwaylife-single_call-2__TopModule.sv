module TopModule (
    input  wire         clk,
    input  wire         load,
    input  wire [255:0] data,
    output reg  [255:0] q
);

    reg [255:0] q_next;

    integer r, c;
    integer dr, dc;
    integer nr, nc;
    integer count;

    always @(*) begin
        for (r = 0; r < 16; r = r + 1) begin
            for (c = 0; c < 16; c = c + 1) begin
                count = 0;
                for (dr = -1; dr <= 1; dr = dr + 1) begin
                    for (dc = -1; dc <= 1; dc = dc + 1) begin
                        if (!(dr == 0 && dc == 0)) begin
                            nr = (r + dr + 16) % 16;
                            nc = (c + dc + 16) % 16;
                            count = count + q[nr * 16 + nc];
                        end
                    end
                end

                case (count)
                    2: q_next[r * 16 + c] = q[r * 16 + c];
                    3: q_next[r * 16 + c] = 1'b1;
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
