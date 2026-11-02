`timescale 1ns/1ps
// @latency 1
module priority_encoder8_core (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output reg [2:0] index,
    output reg valid
);

wire upper_nonzero;
wire lower_nonzero;
wire [2:0] encoded_index;

assign upper_nonzero = |request[7:4];
assign lower_nonzero = |request[3:0];

assign encoded_index[2] = upper_nonzero;
assign encoded_index[1] =
    (upper_nonzero & (request[7] | request[6])) |
    (!upper_nonzero & (request[3] | request[2]));
assign encoded_index[0] =
    request[7] |
    (!request[6] & request[5]) |
    (!upper_nonzero & request[3]) |
    (!upper_nonzero & !request[2] & request[1]);

always @(posedge clk) begin
    if (rst) begin
        index <= 3'd0;
        valid <= 1'b0;
    end else begin
        index <= encoded_index;
        valid <= upper_nonzero | lower_nonzero;
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