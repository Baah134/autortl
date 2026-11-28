module TopModule (
    input  wire       clk,
    input  wire       reset,
    input  wire [2:0] s,
    output wire       fr2,
    output wire       fr1,
    output wire       fr0,
    output reg        dfr
);

    localparam [1:0] LOWEST = 2'd0,
                     LOWER  = 2'd1,
                     UPPER  = 2'd2,
                     HIGHEST = 2'd3;

    reg [1:0] level;
    reg [1:0] sensed_level;

    always @* begin
        case (s)
            3'b000: sensed_level = LOWEST;
            3'b001: sensed_level = LOWER;
            3'b011: sensed_level = UPPER;
            3'b111: sensed_level = HIGHEST;
            default: sensed_level = level;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            level <= LOWEST;
            dfr   <= 1'b1;
        end else begin
            level <= sensed_level;
            case (sensed_level)
                LOWEST:  dfr <= 1'b1;
                HIGHEST: dfr <= 1'b0;
                default: begin
                    if (sensed_level != level)
                        dfr <= (sensed_level > level);
                end
            endcase
        end
    end

    assign fr2 = (level == LOWEST);
    assign fr1 = (level <= LOWER);
    assign fr0 = (level != HIGHEST);

endmodule
