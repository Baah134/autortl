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

    // Progress values 1 through 8 consume the eight data samples.
    reg [3:0] progress;
    reg done_reg;

    assign done = done_reg;

    always @(posedge clk) begin
        if (reset) begin
            progress <= IDLE;
            done_reg <= 1'b0;
        end else begin
            done_reg <= (progress == STOP) && in;

            case (progress)
                IDLE:           progress <= in ? IDLE : 4'd1;
                STOP, RECOVERY: progress <= in ? IDLE : RECOVERY;
                default:        progress <= progress + 4'd1;
            endcase
        end
    end

endmodule