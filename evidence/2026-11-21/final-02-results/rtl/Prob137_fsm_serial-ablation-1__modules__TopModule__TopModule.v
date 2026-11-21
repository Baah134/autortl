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

    // States 1 through 8 consume the eight data samples.
    (* fsm_encoding = "none" *) reg [3:0] state;
    reg done_reg;

    assign done = done_reg;

    always @(posedge clk) begin
        if (reset) begin
            state    <= IDLE;
            done_reg <= 1'b0;
        end else begin
            done_reg <= (state == STOP) && in;

            case (state)
                IDLE: begin
                    if (!in)
                        state <= state + 4'd1;
                end
                STOP: begin
                    if (in)
                        state <= IDLE;
                    else
                        state <= RECOVERY;
                end
                RECOVERY: begin
                    if (in)
                        state <= IDLE;
                end
                4'd1, 4'd2, 4'd3, 4'd4, 4'd5, 4'd6, 4'd7, 4'd8:
                    state <= state + 4'd1;
                default:
                    state <= IDLE;
            endcase
        end
    end

endmodule