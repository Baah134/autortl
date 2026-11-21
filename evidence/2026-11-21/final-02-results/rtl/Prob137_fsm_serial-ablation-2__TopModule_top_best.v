`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output wire done
);
    localparam [3:0] IDLE     = 4'd0;
    localparam [3:0] STOP     = 4'd9;
    localparam [3:0] RECOVERY = 4'd10;

    // Each pair of 16-bit halves covers in=1 and in=0, respectively.
    // Both functions share the five inputs for dual-output LUT mapping.
    localparam [31:0] STATE_BIT_1 = 32'h6066_6666;
    localparam [31:0] STATE_BIT_3 = 32'h7980_7f80;

    (* fsm_encoding = "none" *) reg [3:0] state;
    reg done_reg;

    wire [3:0] incremented_state;
    wire [4:0] lut_address;
    wire [3:0] next_state;
    wire at_stop;
    wire stop_or_recovery;

    assign done = done_reg;
    assign at_stop = (state == STOP);
    assign stop_or_recovery = at_stop || (state == RECOVERY);
    assign incremented_state = state + 4'd1;
    assign lut_address = {in, state};

    assign next_state[0] = incremented_state[0] &&
                           !stop_or_recovery && ((state != IDLE) || !in);
    assign next_state[1] = STATE_BIT_1[lut_address];
    assign next_state[2] = incremented_state[2] && !stop_or_recovery;
    assign next_state[3] = STATE_BIT_3[lut_address];

    // With reset low, either input advances states 1 through 8 to 2 through 9.
    // In idle, 0 starts at state 1 and 1 holds idle. From stop or recovery,
    // 0 selects recovery and 1 selects idle. Only stop with 1 asserts done.
    // A high recovery sample is consumed, and idle accepts the next start.
    // Reset clears both registers from every state, including a valid stop.
    always @(posedge clk) begin
        if (reset) begin
            state    <= IDLE;
            done_reg <= 1'b0;
        end else begin
            state    <= next_state;
            done_reg <= at_stop && in;
        end
    end
endmodule