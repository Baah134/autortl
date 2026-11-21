`timescale 1ns/1ps
// @latency 0
module TopModule_top (
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    input  wire [7:0] d,
    output wire [7:0] min
);
    // Table indices list the inputs from most to least significant.
    // LESS3 uses {left_group, right_group}.
    // EXTEND_LESS uses {left_group, right_group, lower_less}.
    // SELECT_BIT uses {left_msb, right_msb, less7, left_bit, right_bit}.
    localparam [63:0] LESS3       = 64'h0080_C0E0_F0F8_FCFE;
    localparam [31:0] EXTEND_LESS = 32'h80E0_F8FE;
    localparam [31:0] SELECT_BIT  = 32'hCAAA_CCCA;

    wire [7:0] winner [0:2];

    genvar unit_index;
    genvar bit_index;
    generate
        for (unit_index = 0; unit_index < 3; unit_index = unit_index + 1) begin : compare_select
            wire [7:0] left_operand;
            wire [7:0] right_operand;
            (* keep = "true" *) wire less3;
            (* keep = "true" *) wire less5;
            (* keep = "true" *) wire less7;

            if (unit_index == 0) begin : pair_ab
                assign left_operand  = a;
                assign right_operand = b;
            end else if (unit_index == 1) begin : pair_cd
                assign left_operand  = c;
                assign right_operand = d;
            end else begin : final_pair
                assign left_operand  = winner[0];
                assign right_operand = winner[1];
            end

            assign less3 = LESS3[{left_operand[2:0], right_operand[2:0]}];
            assign less5 = EXTEND_LESS[{left_operand[4:3], right_operand[4:3], less3}];
            assign less7 = EXTEND_LESS[{left_operand[6:5], right_operand[6:5], less5}];

            assign winner[unit_index][7] = left_operand[7] & right_operand[7];

            for (bit_index = 0; bit_index < 7; bit_index = bit_index + 1) begin : select_low_bit
                assign winner[unit_index][bit_index] =
                    SELECT_BIT[{left_operand[7], right_operand[7], less7,
                                left_operand[bit_index], right_operand[bit_index]}];
            end
        end
    endgenerate

    assign min = winner[2];
endmodule