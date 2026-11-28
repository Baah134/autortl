module TopModule (
    input  clk,
    input  areset,
    input  x,
    output z
);

    // State definitions
    // IDLE: Waiting for the first '1' (output 0)
    // OUT1: Current output is 1 (either the first '1' or subsequent '0' inverted)
    // OUT0: Current output is 0 (subsequent '1' inverted)
    localparam [1:0] IDLE = 2'b00,
                     OUT1 = 2'b01,
                     OUT0 = 2'b10;

    reg [1:0] state, next_state;

    // Next-state logic
    always @(*) begin
        case (state)
            IDLE:    next_state = x ? OUT1 : IDLE;
            OUT1:    next_state = x ? OUT0 : OUT1;
            OUT0:    next_state = x ? OUT0 : OUT1;
            default: next_state = IDLE;
        endcase
    end

    // Sequential state register with asynchronous active-high reset
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= IDLE;
        end else begin
            state <= next_state;
        end
    end

    // Moore output logic
    assign z = (state == OUT1);

endmodule
