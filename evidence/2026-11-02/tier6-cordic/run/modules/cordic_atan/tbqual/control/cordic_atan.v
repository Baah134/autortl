`timescale 1ns/1ps
// @latency 0
module cordic_atan (
    input  wire [3:0]  idx,
    output wire [19:0] atan
);

    reg [19:0] atan_value;

    always @(*) begin
        atan_value = 20'd0;
        case (idx)
            4'd0:  atan_value = 20'd131072;
            4'd1:  atan_value = 20'd77376;
            4'd2:  atan_value = 20'd40884;
            4'd3:  atan_value = 20'd20753;
            4'd4:  atan_value = 20'd10417;
            4'd5:  atan_value = 20'd5213;
            4'd6:  atan_value = 20'd2607;
            4'd7:  atan_value = 20'd1304;
            4'd8:  atan_value = 20'd652;
            4'd9:  atan_value = 20'd326;
            4'd10: atan_value = 20'd163;
            4'd11: atan_value = 20'd81;
            4'd12: atan_value = 20'd41;
            4'd13: atan_value = 20'd20;
            4'd14: atan_value = 20'd10;
            4'd15: atan_value = 20'd5;
        endcase
    end

    assign atan = atan_value;

endmodule