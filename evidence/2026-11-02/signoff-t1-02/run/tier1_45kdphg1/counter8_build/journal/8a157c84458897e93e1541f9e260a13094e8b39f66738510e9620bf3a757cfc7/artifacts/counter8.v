`timescale 1ns/1ps
// @latency 1
module counter8_core (
    input wire clk,
    input wire rst,
    input wire enable,
    output wire [7:0] count
);

reg [7:0] count_q;
assign count = count_q;

always @(posedge clk) begin
    if (rst)
        count_q <= 8'd0;
    else
        count_q <= count_q ^ {
            enable & (&count_q[6:0]),
            enable & (&count_q[5:0]),
            enable & (&count_q[4:0]),
            enable & (&count_q[3:0]),
            enable & (&count_q[2:0]),
            enable & (&count_q[1:0]),
            enable & count_q[0],
            enable
        };
end

endmodule

`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module counter8 (
    input wire clk,
    input wire rst,
    input wire enable,
    output wire [7:0] count
);
    counter8_core u_counter8_core (
        .clk(clk),
        .rst(rst),
        .enable(enable),
        .count(count)
    );
endmodule