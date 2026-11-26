module TopModule (
    input  wire clk,
    input  wire areset,
    input  wire x,
    output reg  z
);

    // Moore machine states
    // A serial 2's complementer starting from LSB:
    // - Copy all bits unchanged up to and including the first '1'.
    // - After the first '1' has been output, invert all subsequent bits.
    //
    // For a Moore machine, the output 'z' depends solely on the current state.
    // State S0: Initial state before any '1' has been seen. Output z = 0.
    // State S1: The first '1' was just seen. Output z = 1.
    // State S_INV0: Seen the first '1' previously, and the current bit to output is inverted ('0' -> output '1').
    // State S_INV1: Seen the first '1' previously, and the current bit to output is inverted ('1' -> output '0').

    localparam S0     = 2'b00;
    localparam S1     = 2'b01;
    localparam S_INV0 = 2'b10;
    localparam S_INV1 = 2'b11;

    reg [1:0] state, next_state;

    // State register with asynchronous reset (positive-edge triggered)
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= S0;
        end else begin
            state <= next_state;
        end
    end

    // Next-state logic
    always @(*) begin
        case (state)
            S0: begin
                if (x)
                    next_state = S1;
                else
                    next_state = S0;
            end
            S1, S_INV0, S_INV1: begin
                if (x)
                    next_state = S_INV1; // Invert '1' -> output '0'
                else
                    next_state = S_INV0; // Invert '0' -> output '1'
            end
            default: next_state = S0;
        endcase
    end

    // Moore output logic
    always @(*) begin
        case (state)
            S0:     z = 1'b0;
            S1:     z = 1'b1;
            S_INV0: z = 1'b1;
            S_INV1: z = 1'b0;
            default: z = 1'b0;
        endcase
    end

endmodule
