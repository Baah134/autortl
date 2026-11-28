`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input wire clk,
    input wire reset,
    input wire in,
    output wire done
);
    localparam [3:0] PHASE_STOP = 4'd8;
    localparam [3:0] PHASE_IDLE = 4'd10;

    (* fsm_encoding = "none" *) reg [3:0] phase;
    reg done_reg;

    wire data_phase;
    wire recovery_next;
    wire carry_into_bit2;
    wire [3:0] phase_next;
    wire stop_success;

    assign data_phase = ~phase[3];
    assign recovery_next = ~in & (phase[2:0] != PHASE_IDLE[2:0]);
    assign carry_into_bit2 = phase[1] & phase[0];

    assign phase_next[0] = data_phase ? ~phase[0] : recovery_next;
    assign phase_next[1] = data_phase ? (phase[1] ^ phase[0]) : in;
    assign phase_next[3] = data_phase ? (phase[2] & carry_into_bit2)
                                      : (in | recovery_next);

    // These two D functions share a five-input LUT support.
    assign phase_next[2] = data_phase & (phase[2] ^ carry_into_bit2);
    assign stop_success = (phase == PHASE_STOP) & in;

    assign done = done_reg;

    // For in=0/1, phases 0 through 7 each advance by one with done=0.
    // Phase 8 goes to 9/10 with done=0/1. Phase 9 goes to 9/10
    // with done=0. Phase 10 goes to 0/10 with done=0.
    // Reset sends every phase to 10 and clears done for either input.
    always @(posedge clk) begin
        if (reset) begin
            phase    <= PHASE_IDLE;
            done_reg <= 1'b0;
        end else begin
            phase    <= phase_next;
            done_reg <= stop_success;
        end
    end

    // Physical LUT pairing, harness checks, and routed timing and area
    // remain unverified for this candidate.
endmodule