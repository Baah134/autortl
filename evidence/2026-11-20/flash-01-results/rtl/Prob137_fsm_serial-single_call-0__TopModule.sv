module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output wire done
);

    localparam [3:0]
        IDLE  = 4'd0,
        D0    = 4'd1,
        D1    = 4'd2,
        D2    = 4'd3,
        D3    = 4'd4,
        D4    = 4'd5,
        D5    = 4'd6,
        D6    = 4'd7,
        D7    = 4'd8,
        STOP  = 4'd9,
        DONE  = 4'd10,
        ERROR = 4'd11;

    reg [3:0] state, next_state;

    // State register with synchronous active-high reset
    always @(posedge clk) begin
        if (reset) begin
            state <= IDLE;
        end else begin
            state <= next_state;
        end
    end

    // Next-state logic
    always @(*) begin
        case (state)
            IDLE:    next_state = in ? IDLE : D0;
            D0:      next_state = D1;
            D1:      next_state = D2;
            D2:      next_state = D3;
            D3:      next_state = D4;
            D4:      next_state = D5;
            D5:      next_state = D6;
            D6:      next_state = D7;
            D7:      next_state = STOP;
            STOP:    next_state = in ? DONE : ERROR;
            DONE:    next_state = in ? IDLE : D0;
            ERROR:   next_state = in ? IDLE : ERROR;
            default: next_state = IDLE;
        endcase
    end

    // Output logic
    assign done = (state == DONE);

endmodule
