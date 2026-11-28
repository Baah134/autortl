module TopModule (
    input  wire clk,
    input  wire areset,
    input  wire x,
    output reg  z
);

    // Moore State Machine States
    // In 2's complement (starting from LSB):
    // All bits up to and including the first '1' remain unchanged.
    // All subsequent bits are inverted (~x).
    //
    // Since this is a Moore machine, output z depends only on the current state.
    // S_RESET: Initial reset state (output 0).
    // S_ZERO:  Scanning initial 0s (output 0).
    // S_FIRST: First 1 detected (output 1).
    // S_INV0:  Inverting phase, seen 0 -> output 1 (~0).
    // S_INV1:  Inverting phase, seen 1 -> output 0 (~1).

    localparam S_RESET = 3'd0,
               S_ZERO  = 3'd1,
               S_FIRST = 3'd2,
               S_INV0  = 3'd3,
               S_INV1  = 3'd4;

    reg [2:0] state, next_state;

    // State register with asynchronous reset (active-high positive edge)
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= S_RESET;
        end else begin
            state <= next_state;
        end
    end

    // Next-state logic
    always @(*) begin
        case (state)
            S_RESET: begin
                if (x)
                    next_state = S_FIRST;
                else
                    next_state = S_ZERO;
            end
            S_ZERO: begin
                if (x)
                    next_state = S_FIRST;
                else
                    next_state = S_ZERO;
            end
            S_FIRST, S_INV0, S_INV1: begin
                if (x)
                    next_state = S_INV1; // input 1 inverted is 0
                else
                    next_state = S_INV0; // input 0 inverted is 1
            end
            default: begin
                next_state = S_RESET;
            end
        endcase
    end

    // Moore output logic
    always @(*) begin
        case (state)
            S_RESET: z = 1'b0;
            S_ZERO:  z = 1'b0;
            S_FIRST: z = 1'b1;
            S_INV0:  z = 1'b1; // ~0 = 1
            S_INV1:  z = 1'b0; // ~1 = 0
            default: z = 1'b0;
        endcase
    end

endmodule
