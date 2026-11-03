`timescale 1ns/1ps
// @latency 1
module priority_encoder8_core (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);

wire upper_half_any;
wire upper_pair_any;
wire upper_quartet_any;
wire lower_pair_any;
wire [2:0] index_next;

reg [2:0] index_reg;
reg valid_reg;

assign upper_half_any = |request[7:4];
assign upper_pair_any = |request[7:6];
assign upper_quartet_any = |request[7:4];
assign lower_pair_any = |request[3:2];

assign index_next[2] = upper_half_any;
assign index_next[1] = upper_pair_any |
                       (~upper_quartet_any & lower_pair_any);
assign index_next[0] = request[7] |
                       (~(|request[7:6]) & request[5]) |
                       (~(|request[7:4]) & request[3]) |
                       (~(|request[7:2]) & request[1]);

assign index = index_reg;
assign valid = valid_reg;

always @(posedge clk) begin
    if (rst) begin
        index_reg <= 3'd0;
        valid_reg <= 1'b0;
    end else begin
        index_reg <= index_next;
        valid_reg <= |request;
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