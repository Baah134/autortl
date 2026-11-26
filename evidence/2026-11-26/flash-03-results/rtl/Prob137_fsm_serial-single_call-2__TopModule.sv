module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output wire done
);

    localparam IDLE  = 3'd0;
    localparam DATA  = 3'd1;
    localparam STOP  = 3'd2;
    localparam ERROR = 3'd3;

    reg [2:0] state, next_state;
    reg [2:0] bit_cnt;

    // State register and bit counter
    always @(posedge clk) begin
        if (reset) begin
            state   <= IDLE;
            bit_cnt <= 3'd0;
        end else begin
            state <= next_state;
            if (state == DATA) begin
                bit_cnt <= bit_cnt + 3'd1;
            end else begin
                bit_cnt <= 3'd0;
            end
        end
    end

    // Next state logic
    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (~in)
                    next_state = DATA;
                else
                    next_state = IDLE;
            end
            DATA: begin
                if (bit_cnt == 3'd7)
                    next_state = STOP;
                else
                    next_state = DATA;
            end
            STOP: begin
                if (in) begin
                    // Stop bit is correct (1).
                    // If a new start bit immediately follows, go to DATA; else IDLE.
                    next_state = IDLE;
                end else begin
                    // Missing stop bit, wait for a stop bit (1)
                    next_state = ERROR;
                end
            end
            ERROR: begin
                if (in)
                    next_state = IDLE;
                else
                    next_state = ERROR;
            end
            default: next_state = IDLE;
        endcase
    end

    // done is asserted when a byte has been correctly received (at the valid stop bit)
    assign done = (state == STOP) && in;

endmodule
