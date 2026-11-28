`timescale 1ns/1ps
// @latency 1
module priority_encoder8_core (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);

wire group_74_valid;
wire group_70_valid;
wire group_76_valid;
wire group_72_valid;
wire index_bit2;
wire index_bit1;
wire index_bit0;

reg [2:0] index_q;
reg valid_q;

assign group_74_valid = |request[7:4];
assign group_70_valid = |request[7:0];
assign group_76_valid = |request[7:6];
assign group_72_valid = |request[7:2];

assign index_bit2 = group_74_valid;
assign index_bit1 = request[7] | request[6] |
                    (~group_74_valid & (request[3] | request[2]));
assign index_bit0 = request[7] |
                    (~group_76_valid & request[5]) |
                    (~group_74_valid & request[3]) |
                    (~group_72_valid & request[1]);

assign index = index_q;
assign valid = valid_q;

always @(posedge clk) begin
    if (rst) begin
        index_q <= 3'd0;
        valid_q <= 1'b0;
    end else begin
        index_q <= {index_bit2, index_bit1, index_bit0};
        valid_q <= group_70_valid;
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