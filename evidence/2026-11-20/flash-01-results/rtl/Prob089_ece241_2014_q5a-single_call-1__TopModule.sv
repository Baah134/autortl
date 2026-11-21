module TopModule (
    input  clk,
    input  areset,
    input  x,
    output z
);

    localparam S_IDLE = 2'b00; // Output 0, waiting for first 1
    localparam S_ONE  = 2'b01; // Output 1
    localparam S_ZERO = 2'b10; // Output 0, after first 1 has been seen

    reg [1:0] state, next_state;

    // State transition logic
    always @(*) begin
        case (state)
            S_IDLE:  next_state = x ? S_ONE  : S_IDLE;
            S_ONE:   next_state = x ? S_ZERO : S_ONE;
            S_ZERO:  next_state = x ? S_ZERO : S_ONE;
            default: next_state = S_IDLE;
        endcase
    end

    // State register with positive-edge asynchronous reset
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= S_IDLE;
        end else begin
            state <= next_state;
        end
    end

    // Moore output logic: output depends only on the current state
    assign z = (state == S_ONE);

endmodule
