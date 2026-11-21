module TopModule (
    input  wire clk,
    input  wire resetn,
    input  wire x,
    input  wire y,
    output wire f,
    output wire g
);

    localparam [3:0]
        STATE_A = 4'd0,
        STATE_B = 4'd1,
        STATE_C = 4'd2,
        STATE_D = 4'd3,
        STATE_E = 4'd4,
        STATE_F = 4'd5,
        STATE_G = 4'd6,
        STATE_H = 4'd7,
        STATE_I = 4'd8;

    reg [3:0] state, next_state;

    // State transition logic
    always @(*) begin
        case (state)
            STATE_A: begin
                next_state = STATE_B;
            end
            STATE_B: begin
                next_state = STATE_C;
            end
            STATE_C: begin
                if (x)
                    next_state = STATE_D;
                else
                    next_state = STATE_C;
            end
            STATE_D: begin
                if (x)
                    next_state = STATE_D;
                else
                    next_state = STATE_E;
            end
            STATE_E: begin
                if (x)
                    next_state = STATE_F;
                else
                    next_state = STATE_C;
            end
            STATE_F: begin
                if (y)
                    next_state = STATE_H;
                else
                    next_state = STATE_G;
            end
            STATE_G: begin
                if (y)
                    next_state = STATE_H;
                else
                    next_state = STATE_I;
            end
            STATE_H: begin
                next_state = STATE_H;
            end
            STATE_I: begin
                next_state = STATE_I;
            end
            default: begin
                next_state = STATE_A;
            end
        endcase
    end

    // Sequential state register with synchronous active-low reset
    always @(posedge clk) begin
        if (!resetn) begin
            state <= STATE_A;
        end else begin
            state <= next_state;
        end
    end

    // Output logic
    assign f = (state == STATE_B);
    assign g = (state == STATE_F) || (state == STATE_G) || (state == STATE_H);

endmodule
