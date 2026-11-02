`timescale 1ns/1ps
// @latency 1
module priority_encoder8_core (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);

wire upper_half;
wire upper_pair;
wire lower_pair;
wire selected_bit1;
wire selected_bit0;

reg [2:0] index_reg;
reg valid_reg;

assign upper_half = |request[7:4];
assign upper_pair = |request[7:6];
assign lower_pair = |request[3:2];

assign selected_bit1 = upper_half ? upper_pair : lower_pair;
assign selected_bit0 = upper_half
                     ? (upper_pair ? request[7] : request[5])
                     : (lower_pair ? request[3] : request[1]);

assign index = index_reg;
assign valid = valid_reg;

always @(posedge clk) begin
    if (rst) begin
        index_reg <= 3'd0;
        valid_reg <= 1'b0;
    end else begin
        index_reg <= {upper_half, selected_bit1, selected_bit0};
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