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
    reg signed [15:0] data1;
    reg signed [15:0] data2;
    reg signed [15:0] data3;
    reg signed [15:0] data4;
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

    wire signed [26:0] product0 = pair0 * C0;
    wire signed [26:0] product1 = pair1 * C1;
    wire signed [26:0] product2 = pair2 * C2;
    wire signed [26:0] product3 = pair3 * C3;
    wire signed [26:0] product4 = pair4 * C4;
    wire signed [26:0] product5 = pair5 * C5;
    wire signed [26:0] product6 = pair6 * C6;
    wire signed [26:0] product7 = pair7 * C7;

    wire signed [27:0] acc =
        {{1{product0[26]}}, product0} +
        {{1{product1[26]}}, product1} +
        {{1{product2[26]}}, product2} +
        {{1{product3[26]}}, product3} +
        {{1{product4[26]}}, product4} +
        {{1{product5[26]}}, product5} +
        {{1{product6[26]}}, product6} +
        {{1{product7[26]}}, product7};

    wire signed [27:0] rounded = (acc + 28'sd1024) >>> 11;

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
                if (in_valid)
                    data1 <= scaled_sample;
            end
            if (ready2) begin
                valid_slots[1] <= valid_slots[0];
                if (valid_slots[0])
                    data2 <= data1;
            end
            if (ready3) begin
                valid_slots[2] <= valid_slots[1];
                if (valid_slots[1])
                    data3 <= data2;
            end
            if (ready4) begin
                valid_slots[3] <= valid_slots[2];
                if (valid_slots[2])
                    data4 <= data3;
            end
            if (ready5) begin
                valid_slots[4] <= valid_slots[3];
                if (valid_slots[3])
                    data5 <= data4;
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
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
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
