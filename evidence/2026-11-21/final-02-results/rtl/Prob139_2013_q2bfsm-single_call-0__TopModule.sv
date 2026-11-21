module TopModule (
    input  wire clk,
    input  wire resetn,
    input  wire x,
    input  wire y,
    output wire f,
    output wire g
);

    localparam [3:0] A        = 4'd0,
                     PULSE_F  = 4'd1,
                     WAIT_X   = 4'd2,
                     SEEN_1   = 4'd3,
                     SEEN_10  = 4'd4,
                     CHECK_Y1 = 4'd5,
                     CHECK_Y2 = 4'd6,
                     HOLD_G   = 4'd7,
                     CLEAR_G  = 4'd8;

    reg [3:0] state;

    assign f = (state == PULSE_F);
    assign g = (state == CHECK_Y1) || (state == CHECK_Y2) ||
               (state == HOLD_G);

    always @(posedge clk) begin
        if (!resetn) begin
            state <= A;
        end else begin
            case (state)
                A:        state <= PULSE_F;
                PULSE_F:  state <= WAIT_X;
                WAIT_X:   state <= x ? SEEN_1 : WAIT_X;
                SEEN_1:   state <= x ? SEEN_1 : SEEN_10;
                SEEN_10:  state <= x ? CHECK_Y1 : WAIT_X;
                CHECK_Y1: state <= y ? HOLD_G : CHECK_Y2;
                CHECK_Y2: state <= y ? HOLD_G : CLEAR_G;
                HOLD_G:   state <= HOLD_G;
                CLEAR_G:  state <= CLEAR_G;
                default:  state <= A;
            endcase
        end
    end

endmodule
