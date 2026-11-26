module TopModule (
    input  wire       clk,
    input  wire       reset,
    input  wire [2:0] s,
    output reg        fr2,
    output reg        fr1,
    output reg        fr0,
    output reg        dfr
);

    // State definitions
    // Represent the 4 possible sensor regions:
    // S0: Below s[0]             (s == 3'b000)
    // S1: Between s[1] and s[0]  (s == 3'b001)
    // S2: Between s[2] and s[1]  (s == 3'b011)
    // S3: Above s[2]             (s == 3'b111)
    localparam [1:0] LEVEL_0 = 2'd0,
                     LEVEL_1 = 2'd1,
                     LEVEL_2 = 2'd2,
                     LEVEL_3 = 2'd3;

    reg [1:0] current_level;

    wire [1:0] sampled_level;

    // Decode sensor inputs to a level
    assign sampled_level = (s[2]) ? LEVEL_3 :
                           (s[1]) ? LEVEL_2 :
                           (s[0]) ? LEVEL_1 : LEVEL_0;

    always @(posedge clk) begin
        if (reset) begin
            current_level <= LEVEL_0;
            dfr           <= 1'b1;
        end else begin
            if (sampled_level < current_level) begin
                dfr <= 1'b1;
            end else if (sampled_level > current_level) begin
                dfr <= 1'b0;
            end
            // If sampled_level == current_level, dfr retains its previous value

            current_level <= sampled_level;
        end
    end

    // Determine nominal flow outputs based on current_level (or reset condition)
    always @(*) begin
        case (current_level)
            LEVEL_0: begin
                fr0 = 1'b1;
                fr1 = 1'b1;
                fr2 = 1'b1;
            end
            LEVEL_1: begin
                fr0 = 1'b1;
                fr1 = 1'b1;
                fr2 = 1'b0;
            end
            LEVEL_2: begin
                fr0 = 1'b1;
                fr1 = 1'b0;
                fr2 = 1'b0;
            end
            LEVEL_3: begin
                fr0 = 1'b0;
                fr1 = 1'b0;
                fr2 = 1'b0;
            end
            default: begin
                fr0 = 1'b1;
                fr1 = 1'b1;
                fr2 = 1'b1;
            end
        endcase
    end

endmodule
