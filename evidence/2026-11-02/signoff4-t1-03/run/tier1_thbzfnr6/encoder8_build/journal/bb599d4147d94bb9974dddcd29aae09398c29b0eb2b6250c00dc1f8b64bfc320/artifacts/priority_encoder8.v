`timescale 1ns/1ps
// @latency 1
module priority_encoder8_core (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);

wire prefix_7_to_4;
wire prefix_7_to_6;
wire prefix_7_to_2;
wire [2:0] index_next;

reg [2:0] index_reg;
reg valid_reg;

assign prefix_7_to_4 = |request[7:4];
assign prefix_7_to_6 = |request[7:6];
assign prefix_7_to_2 = |request[7:2];

assign index_next[2] = prefix_7_to_4;
assign index_next[1] = prefix_7_to_6 |
                       (~prefix_7_to_4 & (|request[3:2]));
assign index_next[0] = request[7] |
                       (~prefix_7_to_6 & request[5]) |
                       (~prefix_7_to_4 & request[3]) |
                       (~prefix_7_to_2 & request[1]);

assign index = index_reg;
assign valid = valid_reg;

always @(posedge clk) begin
    if (rst) begin
        index_reg <= 3'd0;
        valid_reg <= 1'b0;
    end else begin
        index_reg <= index_next;
        valid_reg <= (request != 8'd0);
    end
end

endmodule

`timescale 1ns/1ps
// @latency 1
// Inherited fixed logical latency from transparent typed child wiring; not measured timing.
module priority_encoder8 (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);
    priority_encoder8_core u_priority_encoder8_core (
        .clk(clk),
        .rst(rst),
        .request(request),
        .index(index),
        .valid(valid)
    );
endmodule