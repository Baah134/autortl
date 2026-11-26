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

    // Sequential state transition and bit counter
    always @(posedge clk) begin
        if (reset) begin
            state   <= IDLE;
            bit_cnt <= 3'd0;
        end else begin
            state <= next_state;
            if (state == DATA) begin
                bit_cnt <= bit_cnt + 1'b1;
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
                if (~in) begin
                    next_state = DATA;
                end
            end

            DATA: begin
                if (bit_cnt == 3'd7) begin
                    next_state = STOP;
                end
            end

            STOP: begin
                if (in) begin
                    next_state = IDLE;
                end else begin
                    next_state = ERROR;
                end
            end

            ERROR: begin
                if (in) begin
                    next_state = IDLE;
                end
            end

            default: begin
                next_state = IDLE;
            end
        endcase
    end

    // Output logic
    always @(*) begin
        done = (state == STOP) && in;
    end

endmodule
