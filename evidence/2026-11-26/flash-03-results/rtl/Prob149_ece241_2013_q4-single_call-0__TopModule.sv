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
    reg       dfr_state;

    wire [1:0] next_level = s[2] ? 2'd3 :
                            s[1] ? 2'd2 :
                            s[0] ? 2'd1 : 2'd0;

    always @(posedge clk) begin
        if (reset) begin
            level     <= 2'd0;
            dfr_state <= 1'b1;
        end else begin
            level <= next_level;
            if (next_level == 2'd0) begin
                dfr_state <= 1'b1;
            end else if (next_level == 2'd3) begin
                dfr_state <= 1'b0;
            end else if (next_level > level) begin
                dfr_state <= 1'b1;
            end else if (next_level < level) begin
                dfr_state <= 1'b0;
            end
        end
    end

    always @(*) begin
        dfr = dfr_state;
        case (level)
            2'd0:    {fr2, fr1, fr0} = 3'b111;
            2'd1:    {fr2, fr1, fr0} = 3'b011;
            2'd2:    {fr2, fr1, fr0} = 3'b001;
            2'd3:    {fr2, fr1, fr0} = 3'b000;
            default: {fr2, fr1, fr0} = 3'b000;
        endcase
    end

endmodule
