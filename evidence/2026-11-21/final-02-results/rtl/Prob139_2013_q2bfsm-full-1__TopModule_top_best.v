`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input wire clk,
    input wire resetn,
    input wire x,
    input wire y,
    output wire f,
    output wire g
);

    localparam [2:0] A          = 3'b000;
    localparam [2:0] SEARCH     = 3'b001;
    localparam [2:0] PREFIX_1   = 3'b010;
    localparam [2:0] PREFIX_10  = 3'b011;
    localparam [2:0] SAMPLE_Y1  = 3'b100;
    localparam [2:0] SAMPLE_Y2  = 3'b111;
    localparam [2:0] HOLD       = 3'b110;

    (* fsm_encoding = "none" *) reg [2:0] state;
    reg f_reg;
    reg g_reg;
    reg [1:0] next_low;

    wire next_f;
    wire next_msb;
    wire next_g;

    assign f = f_reg;
    assign g = g_reg;

    // These functions fit the shared five-input set of a dual-output LUT.
    // Physical packing depends on Vivado mapping and is unverified.
    assign next_f = resetn & (state == A);
    assign next_msb = resetn &
                      ((state == SAMPLE_Y1) | (state == SAMPLE_Y2) |
                       (state == HOLD) | ((state == PREFIX_10) & x));

    assign next_g = resetn &
                    ((&state[1:0]) ? (state[2] ? y : x) :
                     ((state == 3'b101) ? 1'b0 : g_reg));

    always @(*) begin
        next_low = A[1:0];
        if (resetn) begin
            case (state)
                A:          next_low = SEARCH[1:0];
                SEARCH:     next_low = x ? PREFIX_1[1:0] : SEARCH[1:0];
                PREFIX_1:   next_low = x ? PREFIX_1[1:0] : PREFIX_10[1:0];
                PREFIX_10:  next_low = x ? SAMPLE_Y1[1:0] : SEARCH[1:0];
                SAMPLE_Y1:  next_low = y ? HOLD[1:0] : SAMPLE_Y2[1:0];
                SAMPLE_Y2:  next_low = HOLD[1:0];
                HOLD:       next_low = HOLD[1:0];
                default:    next_low = A[1:0];
            endcase
        end
    end

    always @(posedge clk) begin
        state <= {next_msb, next_low};
        f_reg <= next_f;
        g_reg <= next_g;
    end

    // Manual edge check against the typed behavior, with outputs
    // observed after each rising edge.
    // Reset from each reachable state, including both HOLD outcomes,
    // yields A and f=g=0 for every binary x,y pair.
    // With reset released, x=1|101 gives f=1000 and g=0001.
    // The bar marks the end of the pulse edge. An early x sampler
    // detects on 1|01, while a late x sampler misses 1|101.
    // After the pulse, x=1101 detects on edge 4. x=100101 detects
    // on edge 6 because the failed 10 prefix clears on edge 3.
    // On detection and the next three edges, y=1000 gives g=1100,
    // catching an early y window or early clear. y=0100 gives
    // g=1111, catching a late window. y=0010 gives g=1111,
    // catching omission of the second sample or a late assertion.
    // Reset with x=1 in PREFIX_10 or y=1 in SAMPLE_Y2 gives g=0,
    // catching sample-over-reset priority. Reset in A gives f=0,
    // catching pulse-over-reset priority.
endmodule