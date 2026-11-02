`timescale 1ns/1ps
// @latency 1
module priority_encoder8_core (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);

    wire upper_any;
    wire bits_7_or_6;
    wire bits_7_to_2_any;

    reg [2:0] index_reg;
    reg valid_reg;

    assign upper_any = |request[7:4];
    assign bits_7_or_6 = request[7] | request[6];
    assign bits_7_to_2_any = |request[7:2];

    assign index = index_reg;
    assign valid = valid_reg;

    always @(posedge clk) begin
        if (rst) begin
            index_reg <= 3'd0;
            valid_reg <= 1'b0;
        end else begin
            valid_reg <= |request;
            index_reg[2] <= upper_any;
            index_reg[1] <= bits_7_or_6 |
                             (~upper_any & (request[3] | request[2]));
            index_reg[0] <= request[7] |
                             (request[5] & ~bits_7_or_6) |
                             (request[3] & ~upper_any) |
                             (request[1] & ~bits_7_to_2_any);
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