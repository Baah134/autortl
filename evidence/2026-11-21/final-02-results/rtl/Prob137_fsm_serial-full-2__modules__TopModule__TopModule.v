`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output wire done
);

    localparam [3:0] IDLE       = 4'd0;
    localparam [3:0] FIRST_DATA = 4'd1;
    localparam [3:0] LAST_DATA  = 4'd8;
    localparam [3:0] STOP       = 4'd9;
    localparam [3:0] RECOVERY   = 4'd10;

    (* fsm_encoding = "none" *) reg [3:0] progress;
    reg done_reg;

    assign done = done_reg;

    always @(posedge clk) begin
        if (reset) begin
            progress <= IDLE;
            done_reg <= 1'b0;
        end else begin
            done_reg <= 1'b0;

            case (progress)
                IDLE: begin
                    if (!in)
                        progress <= FIRST_DATA;
                end

                STOP: begin
                    done_reg <= in;
                    progress <= in ? IDLE : RECOVERY;
                end

                RECOVERY: begin
                    if (in)
                        progress <= IDLE;
                end

                default: begin
                    if (progress <= LAST_DATA)
                        progress <= progress + 4'd1;
                    else
                        progress <= IDLE;
                end
            endcase
        end
    end

endmodule