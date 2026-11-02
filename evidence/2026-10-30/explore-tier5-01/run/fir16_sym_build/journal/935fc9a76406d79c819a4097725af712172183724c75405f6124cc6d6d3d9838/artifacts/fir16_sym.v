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

    reg signed [16:0] pair1_0;
    reg signed [16:0] pair1_1;
    reg signed [16:0] pair1_2;
    reg signed [16:0] pair1_3;
    reg signed [16:0] pair1_4;
    reg signed [16:0] pair1_5;
    reg signed [16:0] pair1_6;
    reg signed [16:0] pair1_7;

    reg signed [26:0] data2_0;
    reg signed [26:0] data2_1;
    reg signed [26:0] data2_2;
    reg signed [26:0] data2_3;
    reg signed [26:0] data2_4;
    reg signed [26:0] data2_5;
    reg signed [26:0] data2_6;
    reg signed [26:0] data2_7;

    reg signed [27:0] data3_0;
    reg signed [27:0] data3_1;
    reg signed [27:0] data3_2;
    reg signed [27:0] data3_3;

    reg signed [28:0] data4_0;
    reg signed [28:0] data4_1;

    reg signed [15:0] data5;
    reg signed [15:0] history [0:14];

    wire ready5 = !valid_slots[4] || out_ready;
    wire ready4 = !valid_slots[3] || ready5;
    wire ready3 = !valid_slots[2] || ready4;
    wire ready2 = !valid_slots[1] || ready3;
    wire ready1 = !valid_slots[0] || ready2;

    assign in_ready = ready1;
    assign out_valid = valid_slots[4];
    assign out_sample = data5;

    localparam signed [9:0] C0 = -10'sd6;
    localparam signed [9:0] C1 = -10'sd20;
    localparam signed [9:0] C2 = -10'sd24;
    localparam signed [9:0] C3 = 10'sd18;
    localparam signed [9:0] C4 = 10'sd110;
    localparam signed [9:0] C5 = 10'sd226;
    localparam signed [9:0] C6 = 10'sd330;
    localparam signed [9:0] C7 = 10'sd390;

    wire signed [16:0] pair0 =
        {in_sample[15], in_sample} + {history[14][15], history[14]};
    wire signed [16:0] pair1 =
        {history[0][15], history[0]} + {history[13][15], history[13]};
    wire signed [16:0] pair2 =
        {history[1][15], history[1]} + {history[12][15], history[12]};
    wire signed [16:0] pair3 =
        {history[2][15], history[2]} + {history[11][15], history[11]};
    wire signed [16:0] pair4 =
        {history[3][15], history[3]} + {history[10][15], history[10]};
    wire signed [16:0] pair5 =
        {history[4][15], history[4]} + {history[9][15], history[9]};
    wire signed [16:0] pair6 =
        {history[5][15], history[5]} + {history[8][15], history[8]};
    wire signed [16:0] pair7 =
        {history[6][15], history[6]} + {history[7][15], history[7]};

    wire signed [26:0] product0 = pair1_0 * C0;
    wire signed [26:0] product1 = pair1_1 * C1;
    wire signed [26:0] product2 = pair1_2 * C2;
    wire signed [26:0] product3 = pair1_3 * C3;
    wire signed [26:0] product4 = pair1_4 * C4;
    wire signed [26:0] product5 = pair1_5 * C5;
    wire signed [26:0] product6 = pair1_6 * C6;
    wire signed [26:0] product7 = pair1_7 * C7;

    wire signed [27:0] sum01 =
        {product0[26], product0} + {product1[26], product1};
    wire signed [27:0] sum23 =
        {product2[26], product2} + {product3[26], product3};
    wire signed [27:0] sum45 =
        {product4[26], product4} + {product5[26], product5};
    wire signed [27:0] sum67 =
        {product6[26], product6} + {product7[26], product7};

    wire signed [28:0] group0123 =
        {data3_0[27], data3_0} + {data3_1[27], data3_1};
    wire signed [28:0] group4567 =
        {data3_2[27], data3_2} + {data3_3[27], data3_3};

    wire signed [29:0] full_accumulator =
        {data4_0[28], data4_0} + {data4_1[28], data4_1};
    wire signed [27:0] accumulator = full_accumulator[27:0];
    wire signed [27:0] rounded = (accumulator + 28'sd1024) >>> 11;

    wire signed [15:0] scaled_sample =
        (rounded > 28'sd32767)  ? 16'sd32767 :
        (rounded < -28'sd32768) ? -16'sd32768 :
                                  rounded[15:0];

    integer i;
    always @(posedge clk) begin
        if (rst) begin
            valid_slots <= 5'b00000;
            for (i = 0; i < 15; i = i + 1)
                history[i] <= 16'sd0;
        end else begin
            if (ready1) begin
                valid_slots[0] <= in_valid;
                if (in_valid) begin
                    pair1_0 <= pair0;
                    pair1_1 <= pair1;
                    pair1_2 <= pair2;
                    pair1_3 <= pair3;
                    pair1_4 <= pair4;
                    pair1_5 <= pair5;
                    pair1_6 <= pair6;
                    pair1_7 <= pair7;
                end
            end

            if (ready2) begin
                valid_slots[1] <= valid_slots[0];
                if (valid_slots[0]) begin
                    data2_0 <= product0;
                    data2_1 <= product1;
                    data2_2 <= product2;
                    data2_3 <= product3;
                    data2_4 <= product4;
                    data2_5 <= product5;
                    data2_6 <= product6;
                    data2_7 <= product7;
                end
            end

            if (ready3) begin
                valid_slots[2] <= valid_slots[1];
                if (valid_slots[1]) begin
                    data3_0 <= sum01;
                    data3_1 <= sum23;
                    data3_2 <= sum45;
                    data3_3 <= sum67;
                end
            end

            if (ready4) begin
                valid_slots[3] <= valid_slots[2];
                if (valid_slots[2]) begin
                    data4_0 <= group0123;
                    data4_1 <= group4567;
                end
            end

            if (ready5) begin
                valid_slots[4] <= valid_slots[3];
                if (valid_slots[3])
                    data5 <= scaled_sample;
            end

            if (in_valid && in_ready) begin
                for (i = 14; i > 0; i = i - 1)
                    history[i] <= history[i-1];
                history[0] <= in_sample;
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