module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire w,
    output wire z
);

    localparam [2:0] STATE_A = 3'd0,
                     STATE_B = 3'd1,
                     STATE_C = 3'd2,
                     STATE_D = 3'd3,
                     STATE_E = 3'd4,
                     STATE_F = 3'd5;

    reg [2:0] state, next_state;

    // State flip-flops with synchronous active-high reset
    always @(posedge clk) begin
        if (reset) begin
            state <= STATE_A;
        end else begin
            state <= next_state;
        end
    end

    // State table (combinational next-state logic)
    always @(*) begin
        case (state)
            STATE_A: next_state = w ? STATE_B : STATE_A;
            STATE_B: next_state = w ? STATE_C : STATE_D;
            STATE_C: next_state = w ? STATE_E : STATE_D;
            STATE_D: next_state = w ? STATE_F : STATE_A;
            STATE_E: next_state = w ? STATE_E : STATE_D;
            STATE_F: next_state = w ? STATE_C : STATE_D;
            default: next_state = STATE_A;
        endcase
    end

    // Output logic
    assign z = (state == STATE_E) || (state == STATE_F);

endmodule
