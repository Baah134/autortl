`timescale 1ns/1ps
module mux4 (
    input  wire clk,
    input  wire rst,
    input  wire [7:0] a, b, c, d,
    input  wire [1:0] sel,
    output wire [7:0] y
);
    // Guaranteed three-DSP ALU mapping requires replanning under the
    // prohibition on primitive instantiation. This behavioral mux tree
    // preserves the source behavior; DSP mapping and routed gains are unverified.

    reg select_low;
    reg select_high;
    reg [7:0] y_reg;

    wire [7:0] mux_ab;
    wire [7:0] mux_cd;
    wire [7:0] mux_result;

    always @(*) begin
        select_low  = 1'b1;
        select_high = 1'b1;
        case (sel)
            2'd0: begin
                select_low  = 1'b0;
                select_high = 1'b0;
            end
            2'd1: begin
                select_low  = 1'b1;
                select_high = 1'b0;
            end
            2'd2: begin
                select_low  = 1'b0;
                select_high = 1'b1;
            end
            default: begin
                select_low  = 1'b1;
                select_high = 1'b1;
            end
        endcase
    end

    assign mux_ab     = select_low  ? b : a;
    assign mux_cd     = select_low  ? d : c;
    assign mux_result = select_high ? mux_cd : mux_ab;

    always @(posedge clk) begin
        if (rst)
            y_reg <= 8'd0;
        else
            y_reg <= mux_result;
    end

    assign y = y_reg;
endmodule