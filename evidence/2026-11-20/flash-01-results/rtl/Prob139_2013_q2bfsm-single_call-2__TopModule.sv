module TopModule (
    input  wire clk,
    input  wire resetn,
    input  wire x,
    input  wire y,
    output wire f,
    output wire g
);

    localparam [3:0]
        A      = 4'd0,
        B      = 4'd1,
        C      = 4'd2,
        D      = 4'd3,
        E      = 4'd4,
        Y1     = 4'd5,
        Y2     = 4'd6,
        Y_HIGH = 4'd7,
        Y_LOW  = 4'd8;

    reg [3:0] state, next_state;

    always @(posedge clk) begin
        if (!resetn)
            state <= A;
        else
            state <= next_state;
    end

    always @(*) begin
        case (state)
            A:       next_state = B;
            B:       next_state = C;
            C:       next_state = x ? D : C;
            D:       next_state = x ? D : E;
            E:       next_state = x ? Y1 : C;
            Y1:      next_state = y ? Y_HIGH : Y2;
            Y2:      next_state = y ? Y_HIGH : Y_LOW;
            Y_HIGH:  next_state = Y_HIGH;
            Y_LOW:   next_state = Y_LOW;
            default: next_state = A;
        endcase
    end

    assign f = (state == B);
    assign g = (state == Y1) || (state == Y2) || (state == Y_HIGH);

endmodule
