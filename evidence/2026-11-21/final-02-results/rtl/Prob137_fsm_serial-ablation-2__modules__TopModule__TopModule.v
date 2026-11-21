`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output wire done
);
    localparam [3:0] IDLE     = 4'd0;
    localparam [3:0] STOP     = 4'd9;
    localparam [3:0] RECOVERY = 4'd10;

    reg [3:0] state;
    reg done_reg;

    assign done = done_reg;

    always @(posedge clk) begin
        if (reset) begin
            state    <= IDLE;
            done_reg <= 1'b0;
        end else begin
            done_reg <= (state == STOP) && in;

            case (state)
                STOP:     state <= in ? IDLE : RECOVERY;
                RECOVERY: state <= in ? IDLE : RECOVERY;
                default: begin
                    // Advance on a start bit and through all eight data bits.
                    if ((state != IDLE) || !in)
                        state <= state + 4'd1;
                end
            endcase
        end
    end
endmodule