module TopModule (
    input  wire       clk,
    input  wire       reset,
    input  wire [2:0] s,
    output reg        fr2,
    output reg        fr1,
    output reg        fr0,
    output reg        dfr
);

    localparam [1:0] BELOW_LOWEST = 2'd0,
                     LOWER_BAND   = 2'd1,
                     UPPER_BAND   = 2'd2,
                     ABOVE_HIGHEST = 2'd3;

    reg [1:0] level;
    reg [1:0] sensed_level;
    reg rose_on_last_change;

    always @* begin
        case (s)
            3'b000: sensed_level = BELOW_LOWEST;
            3'b001: sensed_level = LOWER_BAND;
            3'b011: sensed_level = UPPER_BAND;
            3'b111: sensed_level = ABOVE_HIGHEST;
            default: sensed_level = level;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            level <= BELOW_LOWEST;
            rose_on_last_change <= 1'b0;
        end else if (sensed_level != level) begin
            level <= sensed_level;
            rose_on_last_change <= (sensed_level > level);
        end
    end

    always @* begin
        case (level)
            BELOW_LOWEST:  {fr2, fr1, fr0, dfr} = 4'b1111;
            LOWER_BAND:    {fr2, fr1, fr0, dfr} = {3'b011, rose_on_last_change};
            UPPER_BAND:    {fr2, fr1, fr0, dfr} = {3'b001, rose_on_last_change};
            ABOVE_HIGHEST: {fr2, fr1, fr0, dfr} = 4'b0000;
            default:       {fr2, fr1, fr0, dfr} = 4'b1111;
        endcase
    end

endmodule
