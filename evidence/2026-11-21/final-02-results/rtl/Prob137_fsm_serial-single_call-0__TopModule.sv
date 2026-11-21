module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output reg  done
);

    localparam [1:0] IDLE     = 2'd0,
                     DATA     = 2'd1,
                     STOP     = 2'd2,
                     RECOVERY = 2'd3;

    reg [1:0] state;
    reg [2:0] bit_count;

    always @(posedge clk) begin
        if (reset) begin
            state     <= IDLE;
            bit_count <= 3'd0;
            done      <= 1'b0;
        end else begin
            done <= 1'b0;

            case (state)
                IDLE: begin
                    if (!in) begin
                        bit_count <= 3'd0;
                        state     <= DATA;
                    end
                end

                DATA: begin
                    if (bit_count == 3'd7)
                        state <= STOP;
                    else
                        bit_count <= bit_count + 3'd1;
                end

                STOP: begin
                    if (in) begin
                        done  <= 1'b1;
                        state <= IDLE;
                    end else begin
                        state <= RECOVERY;
                    end
                end

                RECOVERY: begin
                    if (in)
                        state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
