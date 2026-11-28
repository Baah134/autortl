`timescale 1ns/1ps
// @latency 1
module counter8_core (
    input wire clk,
    input wire rst,
    input wire enable,
    output wire [7:0] count
);

reg [7:0] count_reg;
wire [7:0] toggle;

assign count = count_reg;
assign toggle[0] = enable;
assign toggle[1] = enable & (&count_reg[0:0]);
assign toggle[2] = enable & (&count_reg[1:0]);
assign toggle[3] = enable & (&count_reg[2:0]);
assign toggle[4] = enable & (&count_reg[3:0]);
assign toggle[5] = enable & (&count_reg[4:0]);
assign toggle[6] = enable & (&count_reg[5:0]);
assign toggle[7] = enable & (&count_reg[6:0]);

always @(posedge clk) begin
    if (rst)
        count_reg <= 8'b0;
    else
        count_reg <= count_reg ^ toggle;
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