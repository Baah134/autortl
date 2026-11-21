module TopModule (
    input  wire       clk,
    input  wire       reset,
    input  wire [2:0] s,
    output wire       fr2,
    output wire       fr1,
    output wire       fr0,
    output wire       dfr
);

    // State definitions
    // S0  : Below s[0]
    // S1_L: Between s[1] and s[0], previous level was lower
    // S1_H: Between s[1] and s[0], previous level was higher
    // S2_L: Between s[2] and s[1], previous level was lower
    // S2_H: Between s[2] and s[1], previous level was higher
    // S3  : Above s[2]
    localparam [2:0] S0   = 3'd0,
                     S1_L = 3'd1,
                     S1_H = 3'd2,
                     S2_L = 3'd3,
                     S2_H = 3'd4,
                     S3   = 3'd5;

    reg [2:0] state, next_state;

    // State transition logic
    always @(*) begin
        case (state)
            S0: begin
                case (s)
                    3'b000:  next_state = S0;
                    3'b001:  next_state = S1_L; // 0 < 1: previous level lower
                    3'b011:  next_state = S2_L; // 0 < 2: previous level lower
                    3'b111:  next_state = S3;
                    default: next_state = S0;
                endcase
            end

            S1_L: begin
                case (s)
                    3'b000:  next_state = S0;
                    3'b001:  next_state = S1_L;
                    3'b011:  next_state = S2_L; // 1 < 2: previous level lower
                    3'b111:  next_state = S3;
                    default: next_state = S1_L;
                endcase
            end

            S1_H: begin
                case (s)
                    3'b000:  next_state = S0;
                    3'b001:  next_state = S1_H;
                    3'b011:  next_state = S2_L; // 1 < 2: previous level lower
                    3'b111:  next_state = S3;
                    default: next_state = S1_H;
                endcase
            end

            S2_L: begin
                case (s)
                    3'b000:  next_state = S0;
                    3'b001:  next_state = S1_H; // 2 > 1: previous level higher
                    3'b011:  next_state = S2_L;
                    3'b111:  next_state = S3;
                    default: next_state = S2_L;
                endcase
            end

            S2_H: begin
                case (s)
                    3'b000:  next_state = S0;
                    3'b001:  next_state = S1_H; // 2 > 1: previous level higher
                    3'b011:  next_state = S2_H;
                    3'b111:  next_state = S3;
                    default: next_state = S2_H;
                endcase
            end

            S3: begin
                case (s)
                    3'b000:  next_state = S0;
                    3'b001:  next_state = S1_H; // 3 > 1: previous level higher
                    3'b011:  next_state = S2_H; // 3 > 2: previous level higher
                    3'b111:  next_state = S3;
                    default: next_state = S3;
                endcase
            end

            default: next_state = S0;
        endcase
    end

    // Synchronous state register with active-high synchronous reset
    always @(posedge clk) begin
        if (reset) begin
            state <= S0;
        end else begin
            state <= next_state;
        end
    end

    // Moore output logic
    assign fr0 = (state == S0) || (state == S1_L) || (state == S1_H) || (state == S2_L) || (state == S2_H);
    assign fr1 = (state == S0) || (state == S1_L) || (state == S1_H);
    assign fr2 = (state == S0);
    assign dfr = (state == S0) || (state == S1_L) || (state == S2_L);

endmodule
