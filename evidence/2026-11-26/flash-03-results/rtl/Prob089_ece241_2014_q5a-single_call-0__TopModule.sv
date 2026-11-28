module TopModule (
    input  wire clk,
    input  wire areset,
    input  wire x,
    output reg  z
);

    // Moore State Encoding
    // S_RESET: Initial reset state (output 0)
    // S0: Saw only 0s, waiting for the first 1 (output 0)
    // S1: Saw the first 1 (output 1)
    // S_INV0: After first 1, current inverted bit is 0 (input was 1) -> output 0
    // S_INV1: After first 1, current inverted bit is 1 (input was 0) -> output 1
    localparam S_RESET = 3'd0;
    localparam S0      = 3'd1;
    localparam S1      = 3'd2;
    localparam S_INV0  = 3'd3;
    localparam S_INV1  = 3'd4;

    reg [2:0] state, next_state;

    // State transition logic
    always @(*) begin
        case (state)
            S_RESET: begin
                if (x)
                    next_state = S1;
                else
                    next_state = S0;
            end

            S0: begin
                if (x)
                    next_state = S1;
                else
                    next_state = S0;
            end

            S1, S_INV0, S_INV1: begin
                if (x)
                    next_state = S_INV0; // Invert: input 1 -> output 0
                else
                    next_state = S_INV1; // Invert: input 0 -> output 1
            end

            default: next_state = S_RESET;
        endcase
    end

    // State register with asynchronous reset
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= S_RESET;
        end else begin
            state <= next_state;
        end
    end

    // Moore output logic
    always @(*) begin
        case (state)
            S_RESET: z = 1'b0;
            S0:      z = 1'b0;
            S1:      z = 1'b1;
            S_INV0:  z = 1'b0;
            S_INV1:  z = 1'b1;
            default: z = 1'b0;
        endcase
    end

endmodule
