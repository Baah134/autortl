module TopModule (
    input  wire       clk,
    input  wire       reset,
    input  wire [2:0] s,
    output reg        fr2,
    output reg        fr1,
    output reg        fr0,
    output reg        dfr
);

    // State encoding based on water level
    localparam LEVEL_BELOW_S0 = 2'd0;
    localparam LEVEL_S0_S1    = 2'd1;
    localparam LEVEL_S1_S2    = 2'd2;
    localparam LEVEL_ABOVE_S2 = 2'd3;

    reg [1:0] current_level;
    reg [1:0] prev_level;

    // Decode current sensor inputs to water level
    always @(*) begin
        case (s)
            3'b111:  current_level = LEVEL_ABOVE_S2;
            3'b011:  current_level = LEVEL_S1_S2;
            3'b001:  current_level = LEVEL_S0_S1;
            default: current_level = LEVEL_BELOW_S0;
        endcase
    end

    // Sequential state update
    always @(posedge clk) begin
        if (reset) begin
            prev_level <= LEVEL_BELOW_S0;
            dfr        <= 1'b1;
        end else begin
            prev_level <= current_level;
            if (current_level < prev_level) begin
                dfr <= 1'b1;
            end else if (current_level > prev_level) begin
                dfr <= 1'b0;
            end else begin
                dfr <= dfr;
            end
        end
    end

    // Nominal flow rate outputs combinationally driven by current level
    always @(*) begin
        case (current_level)
            LEVEL_ABOVE_S2: begin
                fr0 = 1'b0;
                fr1 = 1'b0;
                fr2 = 1'b0;
            end
            LEVEL_S1_S2: begin
                fr0 = 1'b1;
                fr1 = 1'b0;
                fr2 = 1'b0;
            end
            LEVEL_S0_S1: begin
                fr0 = 1'b1;
                fr1 = 1'b1;
                fr2 = 1'b0;
            end
            default: begin // LEVEL_BELOW_S0
                fr0 = 1'b1;
                fr1 = 1'b1;
                fr2 = 1'b1;
            end
        endcase
    end

endmodule
