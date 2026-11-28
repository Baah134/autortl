module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire w,
    output wire z
);

    // State encoding definition
    localparam [2:0] A = 3'd0,
                     B = 3'd1,
                     C = 3'd2,
                     D = 3'd3,
                     E = 3'd4,
                     F = 3'd5;

    reg [2:0] state, next_state;

    // State flip-flops with synchronous active-high reset
    always @(posedge clk) begin
        if (reset) begin
            state <= A;
        end else begin
            state <= next_state;
        end
    end

    // State table (next-state logic)
    always @(*) begin
        case (state)
            A: next_state = w ? B : A;
            B: next_state = w ? C : D;
            C: next_state = w ? E : D;
            D: next_state = w ? F : A;
            E: next_state = w ? E : D;
            F: next_state = w ? C : D;
            default: next_state = A;
        endcase
    end

    // Output logic: z is 1 in states E and F, and 0 in states A, B, C, and D
    assign z = (state == E) || (state == F);

endmodule
