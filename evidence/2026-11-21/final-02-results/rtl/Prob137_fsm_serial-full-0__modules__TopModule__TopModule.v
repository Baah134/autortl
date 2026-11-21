`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output wire done
);

    localparam [3:0] PHASE_DATA0    = 4'd0;
    localparam [3:0] PHASE_STOP     = 4'd8;
    localparam [3:0] PHASE_RECOVERY = 4'd9;
    localparam [3:0] PHASE_IDLE     = 4'd10;

    (* fsm_encoding = "none" *) reg [3:0] phase;
    reg done_reg;

    wire data_phase;
    wire stop_phase;
    wire idle_phase;

    assign data_phase = !phase[3];
    assign stop_phase = (phase == PHASE_STOP);
    assign idle_phase = (phase == PHASE_IDLE);
    assign done = done_reg;

    always @(posedge clk) begin
        if (reset) begin
            phase    <= PHASE_IDLE;
            done_reg <= 1'b0;
        end else begin
            done_reg <= stop_phase && in;

            if (data_phase)
                phase <= phase + 4'd1;
            else if (in)
                phase <= PHASE_IDLE;
            else if (idle_phase)
                phase <= PHASE_DATA0;
            else
                phase <= PHASE_RECOVERY;
        end
    end

endmodule