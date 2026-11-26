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
    localparam STATE_F      = 4'd1; // f = 1 for 1 cycle
    localparam STATE_X_NONE = 4'd2; // Waiting for first '1' of 1,0,1
    localparam STATE_X_1    = 4'd3; // Got '1'
    localparam STATE_X_10   = 4'd4; // Got '1, 0'
    localparam STATE_G_Y1   = 4'd5; // g = 1, check y (cycle 1)
    localparam STATE_G_Y2   = 4'd6; // g = 1, check y (cycle 2)
    localparam STATE_G_PERM = 4'd7; // g = 1 permanently
    localparam STATE_G_ZERO = 4'd8; // g = 0 permanently

    reg [3:0] state, next_state;

    // State transition logic (sequential with synchronous active-low reset)
    always @(posedge clk) begin
        if (!resetn) begin
            state <= STATE_A;
        end else begin
            state <= next_state;
        end
    end

    // Next-state logic
    always @(*) begin
        case (state)
            STATE_A: begin
                // Synchronous reset de-assertion moves to STATE_F on next clock edge
                next_state = STATE_F;
            end

            STATE_F: begin
                // f is 1 in this cycle; next cycle monitor x
                if (x)
                    next_state = STATE_X_1;
                else
                    next_state = STATE_X_NONE;
            end

            STATE_X_NONE: begin
                if (x)
                    next_state = STATE_X_1;
                else
                    next_state = STATE_X_NONE;
            end

            STATE_X_1: begin
                if (x)
                    next_state = STATE_X_1;
                else
                    next_state = STATE_X_10;
            end

            STATE_X_10: begin
                if (x)
                    next_state = STATE_G_Y1;
                else
                    next_state = STATE_X_NONE;
            end

            STATE_G_Y1: begin
                if (y)
                    next_state = STATE_G_PERM;
                else
                    next_state = STATE_G_Y2;
            end

            STATE_G_Y2: begin
                if (y)
                    next_state = STATE_G_PERM;
                else
                    next_state = STATE_G_ZERO;
            end

            STATE_G_PERM: begin
                next_state = STATE_G_PERM;
            end

            STATE_G_ZERO: begin
                next_state = STATE_G_ZERO;
            end

            default: begin
                next_state = STATE_A;
            end
        endcase
    end

    // Output logic
    always @(*) begin
        f = (state == STATE_F);
        g = (state == STATE_G_Y1) || (state == STATE_G_Y2) || (state == STATE_G_PERM);
    end

endmodule
