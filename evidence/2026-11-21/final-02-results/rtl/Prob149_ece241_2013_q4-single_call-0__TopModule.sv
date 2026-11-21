module TopModule (
    input        clk,
    input        reset,
    input  [2:0] s,
    output reg   fr2,
    output reg   fr1,
    output reg   fr0,
    output reg   dfr
);

    reg [1:0] level;
    reg [1:0] sensed_level;
    reg       rose_on_last_change;

    always @* begin
        case (s)
            3'b000: sensed_level = 2'd0;
            3'b001: sensed_level = 2'd1;
            3'b011: sensed_level = 2'd2;
            3'b111: sensed_level = 2'd3;
            default: sensed_level = level;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            level <= 2'd0;
            rose_on_last_change <= 1'b0;
        end else if (sensed_level != level) begin
            level <= sensed_level;
            rose_on_last_change <= sensed_level > level;
        end
    end

    always @* begin
        fr2 = (level == 2'd0);
        fr1 = (level <= 2'd1);
        fr0 = (level <= 2'd2);
        dfr = (level == 2'd0) ||
              ((level == 2'd1 || level == 2'd2) && rose_on_last_change);
    end

endmodule
