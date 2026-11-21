module TopModule (
    input  wire clk,
    input  wire areset,
    input  wire x,
    output wire z
);

    localparam [1:0] BEFORE_ONE  = 2'b00,
                     OUTPUT_ONE  = 2'b01,
                     OUTPUT_ZERO = 2'b10;

    reg [1:0] state;

    always @(posedge clk or posedge areset) begin
        if (areset)
            state <= BEFORE_ONE;
        else begin
            case (state)
                BEFORE_ONE:  state <= x ? OUTPUT_ONE : BEFORE_ONE;
                OUTPUT_ONE,
                OUTPUT_ZERO: state <= x ? OUTPUT_ZERO : OUTPUT_ONE;
                default:     state <= BEFORE_ONE;
            endcase
        end
    end

    assign z = (state == OUTPUT_ONE);

endmodule
