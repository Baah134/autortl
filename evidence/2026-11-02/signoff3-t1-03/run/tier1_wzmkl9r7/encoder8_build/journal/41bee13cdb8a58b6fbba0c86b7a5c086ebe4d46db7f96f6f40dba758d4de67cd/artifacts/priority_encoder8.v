`timescale 1ns/1ps
// @latency 1
module priority_encoder8_core (
    input wire clk,
    input wire rst,
    input wire [7:0] request,
    output wire [2:0] index,
    output wire valid
);

    wire high_nonzero;
    reg [2:0] index_reg;
    reg valid_reg;

    assign high_nonzero = |request[7:4];
    assign index = index_reg;
    assign valid = valid_reg;

    always @(posedge clk) begin
        if (rst) begin
            index_reg <= 3'd0;
            valid_reg <= 1'b0;
        end else begin
            index_reg[2] <= high_nonzero;
            index_reg[1] <= (high_nonzero && (request[7] || request[6])) ||
                            (!high_nonzero && (request[3] || request[2]));
            index_reg[0] <= (request[7] || (!request[6] && request[5])) ||
                            (!high_nonzero &&
                             (request[3] || (!request[2] && request[1])));
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