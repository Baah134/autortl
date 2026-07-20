// Two-process FSM template (verified pattern)
module fsm_template (
    input  wire clk,
    input  wire rst,
    input  wire start,
    input  wire done_i,
    output reg  busy,
    output reg  fire
);
    localparam IDLE = 2'd0, RUN = 2'd1, FLUSH = 2'd2;
    reg [1:0] state, state_n;

    always @(posedge clk) begin
        if (rst) state <= IDLE;
        else     state <= state_n;
    end

    always @(*) begin
        state_n = state;   // defaults first
        busy    = 1'b0;
        fire    = 1'b0;
        case (state)
            IDLE:  if (start) begin state_n = RUN; fire = 1'b1; end
            RUN:   begin busy = 1'b1; if (done_i) state_n = FLUSH; end
            FLUSH: state_n = IDLE;
            default: state_n = IDLE;
        endcase
    end
endmodule
