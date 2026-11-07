`timescale 1ns/1ps
// @latency 5
module fir16_sym_core (
    input wire clk,
    input wire rst,
    input wire signed [15:0] in_sample,
    input wire in_valid,
    output wire in_ready,
    output wire signed [15:0] out_sample,
    output wire out_valid,
    input wire out_ready
);

    reg [4:0] valid_slots;
    reg signed [15:0] data5;
    reg signed [15:0] history [0:14];

    wire ready5;
    wire ready4;
    wire ready3;
    wire ready2;
    wire ready1;

    assign ready5 = !valid_slots[4] || out_ready;
    assign ready4 = !valid_slots[3] || ready5;
    assign ready3 = !valid_slots[2] || ready4;
    assign ready2 = !valid_slots[1] || ready3;
    assign ready1 = !valid_slots[0] || ready2;

    assign in_ready = ready1;
    assign out_valid = valid_slots[4];
    assign out_sample = data5;

    reg signed [16:0] pair0;
    reg signed [16:0] pair1;
    reg signed [16:0] pair2;
    reg signed [16:0] pair3;
    reg signed [16:0] pair4;
    reg signed [16:0] pair5;
    reg signed [16:0] pair6;
    reg signed [16:0] pair7;

    reg signed [18:0] product0;
    reg signed [20:0] product1;
    reg signed [20:0] product2;
    reg signed [20:0] product3;
    reg signed [22:0] product4;
    reg signed [23:0] product5;
    reg signed [24:0] product6;
    reg signed [24:0] product7;

    reg signed [21:0] sum01;
    reg signed [21:0] sum23;
    reg signed [24:0] sum45;
    reg signed [25:0] sum67;
    reg signed [26:0] half_acc;

    wire signed [18:0] pair_product0 =
        $signed({{2{pair0[16]}}, pair0}) * -19'sd3;
    wire signed [20:0] pair_product1 =
        $signed({{4{pair1[16]}}, pair1}) * -21'sd10;
    wire signed [20:0] pair_product2 =
        $signed({{4{pair2[16]}}, pair2}) * -21'sd12;
    wire signed [20:0] pair_product3 =
        $signed({{4{pair3[16]}}, pair3}) * 21'sd9;
    wire signed [22:0] pair_product4 =
        $signed({{6{pair4[16]}}, pair4}) * 23'sd55;
    wire signed [23:0] pair_product5 =
        $signed({{7{pair5[16]}}, pair5}) * 24'sd113;
    wire signed [24:0] pair_product6 =
        $signed({{8{pair6[16]}}, pair6}) * 25'sd165;
    wire signed [24:0] pair_product7 =
        $signed({{8{pair7[16]}}, pair7}) * 25'sd195;

    wire signed [26:0] rounded = (half_acc + 27'sd512) >>> 10;
    wire signed [15:0] filtered_sample =
        (rounded > 27'sd32767) ? 16'sd32767 :
        (rounded < -27'sd32768) ? -16'sd32768 :
        rounded[15:0];

    integer i;

    always @(posedge clk) begin
        if (rst) begin
            valid_slots <= 5'b00000;
            for (i = 0; i < 15; i = i + 1)
                history[i] <= 16'sd0;
        end else begin
            if (in_valid && in_ready) begin
                for (i = 14; i > 0; i = i - 1)
                    history[i] <= history[i-1];
                history[0] <= in_sample;
            end

            if (ready1) begin
                valid_slots[0] <= in_valid;
                pair0 <= {{1{in_sample[15]}}, in_sample} +
                         {{1{history[14][15]}}, history[14]};
                pair1 <= {{1{history[0][15]}}, history[0]} +
                         {{1{history[13][15]}}, history[13]};
                pair2 <= {{1{history[1][15]}}, history[1]} +
                         {{1{history[12][15]}}, history[12]};
                pair3 <= {{1{history[2][15]}}, history[2]} +
                         {{1{history[11][15]}}, history[11]};
                pair4 <= {{1{history[3][15]}}, history[3]} +
                         {{1{history[10][15]}}, history[10]};
                pair5 <= {{1{history[4][15]}}, history[4]} +
                         {{1{history[9][15]}}, history[9]};
                pair6 <= {{1{history[5][15]}}, history[5]} +
                         {{1{history[8][15]}}, history[8]};
                pair7 <= {{1{history[6][15]}}, history[6]} +
                         {{1{history[7][15]}}, history[7]};
            end

            if (ready2) begin
                valid_slots[1] <= valid_slots[0];
                product0 <= pair_product0;
                product1 <= pair_product1;
                product2 <= pair_product2;
                product3 <= pair_product3;
                product4 <= pair_product4;
                product5 <= pair_product5;
                product6 <= pair_product6;
                product7 <= pair_product7;
            end

            if (ready3) begin
                valid_slots[2] <= valid_slots[1];
                sum01 <= {{3{product0[18]}}, product0} +
                         {{1{product1[20]}}, product1};
                sum23 <= {{1{product2[20]}}, product2} +
                         {{1{product3[20]}}, product3};
                sum45 <= {{2{product4[22]}}, product4} +
                         {{1{product5[23]}}, product5};
                sum67 <= {{1{product6[24]}}, product6} +
                         {{1{product7[24]}}, product7};
            end

            if (ready4) begin
                valid_slots[3] <= valid_slots[2];
                half_acc <= {{5{sum01[21]}}, sum01} +
                            {{5{sum23[21]}}, sum23} +
                            {{2{sum45[24]}}, sum45} +
                            {sum67[25], sum67};
            end

            if (ready5) begin
                valid_slots[4] <= valid_slots[3];
                data5 <= filtered_sample;
            end
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 5
module fir16_sym (
    input wire clk,
    input wire rst,
    input wire signed [15:0] in_sample,
    input wire in_valid,
    output wire in_ready,
    output wire signed [15:0] out_sample,
    output wire out_valid,
    input wire out_ready
);
    fir16_sym_core u_fir16_sym_core (
        .clk(clk),
        .rst(rst),
        .in_sample(in_sample),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_sample(out_sample),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule