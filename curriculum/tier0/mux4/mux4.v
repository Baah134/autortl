module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output reg  [7:0] y
);
    always @(posedge clk) begin
        if (rst) y <= 8'd0;
        else case (sel)
            2'd0: y <= a;
            2'd1: y <= b;
            2'd2: y <= c;
            default: y <= d;
        endcase
    end
endmodule
