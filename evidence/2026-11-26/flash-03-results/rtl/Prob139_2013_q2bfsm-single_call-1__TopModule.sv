module TopModule (
    input  wire clk,
    input  wire resetn,
    input  wire x,
    input  wire y,
    output reg  f,
    output reg  g
);

    // State encoding
    localparam STATE_A      = 4'd0; // Reset state
    localparam STATE_F      = 4'd1; // f = 1 for one cycle
    localparam STATE_X0     = 4'd2; // Waiting for first bit of pattern (1)
    localparam STATE_X1     = 4'd3; // Saw 1
    localparam STATE_X10    = 4'd4; // Saw 1, 0
    localparam STATE_CHECK1 = 4'd5; // g = 1, check y (cycle 1)
    localparam STATE_CHECK2 = 4'd6; // g = 1, check y (cycle 2)
    localparam STATE_G_PERM = 4'd7; // g = 1 permanently
    localparam STATE_STOP   = 4'd8; // g = 0 permanently

    reg [3:0] state, next_state;

    // State register (Synchronous, active-low reset)
    always @(posedge clk) begin
        if (!resetn) begin
            state <= STATE_A;
        end else begin
            state <= next_state;
        end
    end

    // Next-state logic
    always @(*) begin
        next_state = state;
        case (state)
            STATE_A: begin
                // When resetn is de-asserted, move to STATE_F on the next clock edge
                next_state = STATE_F;
            end

            STATE_F: begin
                // f is 1 in this state for one cycle, then monitor x
                if (x)
                    next_state = STATE_X1;
                else
                    next_state = STATE_X0;
            end

            STATE_X0: begin
                if (x)
                    next_state = STATE_X1;
                else
                    next_state = STATE_X0;
            end

            STATE_X1: begin
                if (!x)
                    next_state = STATE_X10;
                else
                    next_state = STATE_X1;
            end

            STATE_X10: begin
                if (x)
                    next_state = STATE_CHECK1;
                else
                    next_state = STATE_X0;
            end

            STATE_CHECK1: begin
                if (y)
                    next_state = STATE_G_PERM;
                else
                    next_state = STATE_CHECK2;
            end

            STATE_CHECK2: begin
                if (y)
                    next_state = STATE_G_PERM;
                else
                    next_state = STATE_STOP;
            end

            STATE_G_PERM: begin
                next_state = STATE_G_PERM;
            end

            STATE_STOP: begin
                next_state = STATE_STOP;
            end

            default: begin
                next_state = STATE_A;
            end
        endcase
    end

    // Output logic
    always @(*) begin
        f = (state == STATE_F);
        g = (state == STATE_CHECK1) || (state == STATE_CHECK2) || (state == STATE_G_PERM);
    end

endmodule
