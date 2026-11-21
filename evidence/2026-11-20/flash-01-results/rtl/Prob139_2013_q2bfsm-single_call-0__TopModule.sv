module TopModule (
    input  clk,
    input  resetn,
    input  x,
    input  y,
    output f,
    output g
);

    localparam [3:0]
        S_A = 4'd0,
        S_B = 4'd1,
        S_C = 4'd2,
        S_D = 4'd3,
        S_E = 4'd4,
        S_F = 4'd5,
        S_G = 4'd6,
        S_H = 4'd7,
        S_I = 4'd8;

    reg [3:0] state, next_state;

    // State transition logic
    always @(*) begin
        case (state)
            S_A:     next_state = S_B;
            S_B:     next_state = S_C;
            S_C:     next_state = x ? S_D : S_C;
            S_D:     next_state = x ? S_D : S_E;
            S_E:     next_state = x ? S_F : S_C;
            S_F:     next_state = y ? S_H : S_G;
            S_G:     next_state = y ? S_H : S_I;
            S_H:     next_state = S_H;
            S_I:     next_state = S_I;
            default: next_state = S_A;
        endcase
    end

    // State register with synchronous active-low reset
    always @(posedge clk) begin
        if (!resetn) begin
            state <= S_A;
        end else begin
            state <= next_state;
        end
    end

    // Output assignments
    assign f = (state == S_B);
    assign g = (state == S_F) || (state == S_G) || (state == S_H);

endmodule
