`timescale 1ns/1ps
// @latency 1
module priority_encoder8_core (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);

wire win7 = request[7];
wire win6 = request[6] & ~request[7];
wire win5 = request[5] & ~(|request[7:6]);
wire win4 = request[4] & ~(|request[7:5]);
wire win3 = request[3] & ~(|request[7:4]);
wire win2 = request[2] & ~(|request[7:3]);
wire win1 = request[1] & ~(|request[7:2]);
wire win0 = request[0] & ~(|request[7:1]);

reg [2:0] index_reg;
reg valid_reg;

assign index = index_reg;
assign valid = valid_reg;

always @(posedge clk) begin
    if (rst) begin
        index_reg <= 3'd0;
        valid_reg <= 1'b0;
    end else begin
        index_reg[2] <= win7 | win6 | win5 | win4;
        index_reg[1] <= win7 | win6 | win3 | win2;
        index_reg[0] <= win7 | win5 | win3 | win1;
        valid_reg <= |request;
    end
end

endmodule

`timescale 1ns/1ps
// @latency 1
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