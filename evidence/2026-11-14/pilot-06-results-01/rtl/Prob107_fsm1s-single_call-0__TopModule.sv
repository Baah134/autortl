module TopModule (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output wire out
);

    localparam A = 1'b0;
    localparam B = 1'b1;

    reg state;

    always @(posedge clk) begin
        if (reset)
            state <= B;
        else if (!in)
            state <= ~state;
    end

    assign out = (state == B);

endmodule
