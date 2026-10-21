`timescale 1ns/1ps
module counter #(
    parameter WIDTH       = 32,
    parameter THRESH_LOW  = 100,
    parameter THRESH_MID  = 500,
    parameter THRESH_HIGH = 1000
)(
    input  wire             clk,
    input  wire             rst,
    input  wire             enable,
    input  wire             load,
    input  wire [WIDTH-1:0] load_val,
    output reg  [WIDTH-1:0] count,
    output reg              at_zero,
    output reg              below_low,
    output reg              below_mid,
    output reg              below_high,
    output reg              overflow
);
    wire [WIDTH:0] increment_result;

    assign increment_result = {1'b0, count} + {{WIDTH{1'b0}}, 1'b1};

    always @(posedge clk) begin
        if (rst) begin
            count    <= {WIDTH{1'b0}};
            overflow <= 1'b0;
        end else if (load) begin
            count    <= load_val;
            overflow <= 1'b0;
        end else if (enable) begin
            count    <= increment_result[WIDTH-1:0];
            overflow <= increment_result[WIDTH];
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            at_zero    <= 1'b1;
            below_low  <= 1'b1;
            below_mid  <= 1'b1;
            below_high <= 1'b1;
        end else begin
            at_zero    <= (count == {WIDTH{1'b0}});
            below_low  <= (count < THRESH_LOW);
            below_mid  <= (count < THRESH_MID);
            below_high <= (count < THRESH_HIGH);
        end
    end
endmodule