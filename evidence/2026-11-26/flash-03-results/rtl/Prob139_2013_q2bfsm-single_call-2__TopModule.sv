module TopModule (
    input  wire clk,
    input  wire resetn,
    input  wire x,
    input  wire y,
    output reg  f,
    output reg  g
);

    // State encoding
    localparam STATE_A      = 4'd0; // Reset / beginning state
    localparam STATE_F      = 4'd1; // f = 1 for 1 cycle
    localparam STATE_X0     = 4'd2; // monitoring x, seen nothing
    localparam STATE_X1     = 4'd3; // seen '1'
    localparam STATE_X10    = 4'd4; // seen '1, 0'
    localparam STATE_Y1     = 4'd5; // g = 1, cycle 1 of checking y
    localparam STATE_Y2     = 4'd6; // g = 1, cycle 2 of checking y
    localparam STATE_G_PERM = 4'd7; // g = 1 permanently until reset
    localparam STATE_G_OFF  = 4'd8; // g = 0 permanently until reset

    reg [3:0] state, next_state;

    // State transition logic
    always @(*) begin
        case (state)
            STATE_A: begin
                next_state = STATE_F;
            end

            STATE_F: begin
                next_state = STATE_X0;
            end

            STATE_X0: begin
                if (x)
                    next_state = STATE_X1;
                else
                    next_state = STATE_X0;
            end

            STATE_X1: begin
                if (x)
                    next_state = STATE_X1;
                else
                    next_state = STATE_X10;
            end

            STATE_X10: begin
                if (x)
                    next_state = STATE_Y1;
                else
                    next_state = STATE_X0;
            end

            STATE_Y1: begin
                if (y)
                    next_state = STATE_G_PERM;
                else
                    next_state = STATE_Y2;
            end

            STATE_Y2: begin
                if (y)
                    next_state = STATE_G_PERM;
                else
                    next_state = STATE_G_OFF;
            end

            STATE_G_PERM: begin
                next_state = STATE_G_PERM;
            end

            STATE_G_OFF: begin
                next_state = STATE_G_OFF;
            end

            default: begin
                next_state = STATE_A;
            end
        endcase
    end

    // Sequential state register
    always @(posedge clk) begin
        if (!resetn) begin
            state <= STATE_A;
        end else begin
            state <= next_state;
        end
    end

    // Output logic
    always @(*) begin
        f = (state == STATE_F);
        g = (state == STATE_Y1) || (state == STATE_Y2) || (state == STATE_G_PERM);
    end

endmodule
