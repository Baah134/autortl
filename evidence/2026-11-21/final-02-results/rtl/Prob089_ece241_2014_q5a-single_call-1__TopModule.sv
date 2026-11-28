module TopModule (
    input  wire clk,
    input  wire areset,
    input  wire x,
    output wire z
);

    localparam [1:0] WAIT_FOR_ONE = 2'b00,
                     OUTPUT_ONE   = 2'b01,
                     OUTPUT_ZERO  = 2'b10;

    reg [1:0] state;

    assign z = (state == OUTPUT_ONE);

    always @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= WAIT_FOR_ONE;
        end else begin
            case (state)
                WAIT_FOR_ONE: state <= x ? OUTPUT_ONE : WAIT_FOR_ONE;
                OUTPUT_ONE,
                OUTPUT_ZERO:  state <= x ? OUTPUT_ZERO : OUTPUT_ONE;
                default:      state <= WAIT_FOR_ONE;
            endcase
        end
    end

endmodule
