module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire x,
    output wire z
);

    reg [2:0] state;
    reg [2:0] next_state;

    // State encoding matching the table
    localparam S000 = 3'b000;
    localparam S001 = 3'b001;
    localparam S010 = 3'b010;
    localparam S011 = 3'b011;
    localparam S100 = 3'b100;

    // Next-state logic
    always @(*) begin
        case (state)
            S000: next_state = x ? 3'b001 : 3'b000;
            S001: next_state = x ? 3'b100 : 3'b001;
            S010: next_state = x ? 3'b001 : 3'b010;
            S011: next_state = x ? 3'b010 : 3'b001;
            S100: next_state = x ? 3'b100 : 3'b011;
            default: next_state = S000;
        endcase
    end

    // Sequential state register with synchronous active-high reset
    always @(posedge clk) begin
        if (reset) begin
            state <= S000;
        end else begin
            state <= next_state;
        end
    end

    // Output logic
    assign z = (state == S011) || (state == S100);

endmodule
