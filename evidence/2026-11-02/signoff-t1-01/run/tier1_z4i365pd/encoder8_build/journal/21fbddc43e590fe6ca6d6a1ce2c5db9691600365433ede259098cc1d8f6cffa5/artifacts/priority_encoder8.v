`timescale 1ns/1ps
// @latency 1
module priority_encoder8_core (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output reg [2:0] index,
    output reg valid
);

always @(posedge clk) begin
    if (rst) begin
        index <= 3'd0;
        valid <= 1'b0;
    end else begin
        valid <= (request != 8'd0);
        if (request[7])      index <= 3'd7;
        else if (request[6]) index <= 3'd6;
        else if (request[5]) index <= 3'd5;
        else if (request[4]) index <= 3'd4;
        else if (request[3]) index <= 3'd3;
        else if (request[2]) index <= 3'd2;
        else if (request[1]) index <= 3'd1;
        else                 index <= 3'd0;
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
