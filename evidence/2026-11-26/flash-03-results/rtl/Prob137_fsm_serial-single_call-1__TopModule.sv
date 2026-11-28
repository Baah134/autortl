module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output reg  done
);

    // State encoding
    localparam IDLE  = 2'd0;
    localparam DATA  = 2'd1;
    localparam STOP  = 2'd2;
    localparam ERROR = 2'd3;

    reg [1:0] state, next_state;
    reg [2:0] bit_cnt;

    // Sequential state transition and counter logic
    always @(posedge clk) begin
        if (reset) begin
            state   <= IDLE;
            bit_cnt <= 3'd0;
            done    <= 1'b0;
        end else begin
            state <= next_state;

            // Increment bit count during DATA state
            if (state == DATA) begin
                bit_cnt <= bit_cnt + 1'b1;
            end else begin
                bit_cnt <= 3'd0;
            end

            // 'done' is asserted when a stop bit is correctly received
            if (state == STOP && in == 1'b1) begin
                done <= 1'b1;
            end else begin
                done <= 1'b0;
            end
        end
    end

    // Next-state combinational logic
    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                // Start bit is 0
                if (~in)
                    next_state = DATA;
                else
                    next_state = IDLE;
            end

            DATA: begin
                // Count 8 data bits (0 to 7)
                if (bit_cnt == 3'd7)
                    next_state = STOP;
                else
                    next_state = DATA;
            end

            STOP: begin
                if (in) begin
                    // Correct stop bit (1) received
                    next_state = IDLE;
                end else begin
                    // Missing stop bit; transition to ERROR state to wait for stop bit
                    next_state = ERROR;
                end
            end

            ERROR: begin
                // Wait until line returns to 1 (stop bit / idle level)
                if (in)
                    next_state = IDLE;
                else
                    next_state = ERROR;
            end

            default: next_state = IDLE;
        endcase
    end

endmodule
