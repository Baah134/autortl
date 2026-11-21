module TopModule (
    input  wire clk,
    input  wire areset,
    input  wire x,
    output wire z
);

    localparam [1:0] WAIT_FOR_ONE = 2'b00,
                     OUTPUT_ZERO  = 2'b10,
                     OUTPUT_ONE   = 2'b11;

    reg [1:0] state;

    always @(posedge clk or posedge areset) begin
        if (areset)
            state <= WAIT_FOR_ONE;
        else begin
            case (state)
                WAIT_FOR_ONE: state <= x ? OUTPUT_ONE : WAIT_FOR_ONE;
                OUTPUT_ZERO,
                OUTPUT_ONE:   state <= x ? OUTPUT_ZERO : OUTPUT_ONE;
                default:      state <= WAIT_FOR_ONE;
            endcase
        end
    end

    assign z = (state == OUTPUT_ONE);

endmodule
