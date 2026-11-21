module TopModule (
    input  clk,
    input  reset,
    input  in,
    output done
);

    localparam IDLE      = 3'd0;
    localparam DATA      = 3'd1;
    localparam STOP      = 3'd2;
    localparam DONE      = 3'd3;
    localparam WAIT_STOP = 3'd4;

    reg [2:0] state, next_state;
    reg [2:0] bit_cnt;

    // Next state logic
    always @(*) begin
        case (state)
            IDLE: begin
                if (!in)
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
                if (in)
                    next_state = DONE;
                else
                    next_state = WAIT_STOP;
            end
            DONE: begin
                if (!in)
                    next_state = DATA;
                else
                    next_state = IDLE;
            end
            WAIT_STOP: begin
                if (in)
                    next_state = IDLE;
                else
                    next_state = WAIT_STOP;
            end
            default: begin
                next_state = IDLE;
            end
        endcase
    end

    // Sequential state and counter register with active-high synchronous reset
    always @(posedge clk) begin
        if (reset) begin
            state   <= IDLE;
            bit_cnt <= 3'd0;
        end else begin
            state <= next_state;
            if (state == DATA) begin
                if (bit_cnt == 3'd7)
                    bit_cnt <= 3'd0;
                else
                    bit_cnt <= bit_cnt + 3'd1;
            end else begin
                bit_cnt <= 3'd0;
            end
        end
    end

    // Output logic
    assign done = (state == DONE);

endmodule
