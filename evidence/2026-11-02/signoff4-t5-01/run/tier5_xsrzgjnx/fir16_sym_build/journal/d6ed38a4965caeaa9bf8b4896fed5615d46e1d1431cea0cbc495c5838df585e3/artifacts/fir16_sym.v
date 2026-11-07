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

    reg signed [27:0] product0;
    reg signed [27:0] product1;
    reg signed [27:0] product2;
    reg signed [27:0] product3;
    reg signed [27:0] product4;
    reg signed [27:0] product5;
    reg signed [27:0] product6;
    reg signed [27:0] product7;
    reg signed [27:0] acc;
    reg signed [27:0] rounded;
    reg signed [15:0] filtered_sample;
    integer i;

    always @(*) begin
        pair0 = 17'sd0;
        pair1 = 17'sd0;
        pair2 = 17'sd0;
        pair3 = 17'sd0;
        pair4 = 17'sd0;
        pair5 = 17'sd0;
        pair6 = 17'sd0;
        pair7 = 17'sd0;

        product0 = 28'sd0;
        product1 = 28'sd0;
        product2 = 28'sd0;
        product3 = 28'sd0;
        product4 = 28'sd0;
        product5 = 28'sd0;
        product6 = 28'sd0;
        product7 = 28'sd0;

        acc = 28'sd0;
        rounded = 28'sd0;
        filtered_sample = 16'sd0;

        pair0 = {{1{in_sample[15]}}, in_sample} +
                {{1{history[14][15]}}, history[14]};
        pair1 = {{1{history[0][15]}}, history[0]} +
                {{1{history[13][15]}}, history[13]};
        pair2 = {{1{history[1][15]}}, history[1]} +
                {{1{history[12][15]}}, history[12]};
        pair3 = {{1{history[2][15]}}, history[2]} +
                {{1{history[11][15]}}, history[11]};
        pair4 = {{1{history[3][15]}}, history[3]} +
                {{1{history[10][15]}}, history[10]};
        pair5 = {{1{history[4][15]}}, history[4]} +
                {{1{history[9][15]}}, history[9]};
        pair6 = {{1{history[5][15]}}, history[5]} +
                {{1{history[8][15]}}, history[8]};
        pair7 = {{1{history[6][15]}}, history[6]} +
                {{1{history[7][15]}}, history[7]};

        product0 = $signed({{11{pair0[16]}}, pair0}) * -28'sd6;
        product1 = $signed({{11{pair1[16]}}, pair1}) * -28'sd20;
        product2 = $signed({{11{pair2[16]}}, pair2}) * -28'sd24;
        product3 = $signed({{11{pair3[16]}}, pair3}) * 28'sd18;
        product4 = $signed({{11{pair4[16]}}, pair4}) * 28'sd110;
        product5 = $signed({{11{pair5[16]}}, pair5}) * 28'sd226;
        product6 = $signed({{11{pair6[16]}}, pair6}) * 28'sd330;
        product7 = $signed({{11{pair7[16]}}, pair7}) * 28'sd390;

        acc = product0 + product1 + product2 + product3 +
              product4 + product5 + product6 + product7;
        rounded = (acc + 28'sd1024) >>> 11;

        if (rounded > 28'sd32767)
            filtered_sample = 16'sd32767;
        else if (rounded < -28'sd32768)
            filtered_sample = -16'sd32768;
        else
            filtered_sample = rounded[15:0];
    end

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
                data1 <= filtered_sample;
            end
            if (ready2) begin
                valid_slots[1] <= valid_slots[0];
                data2 <= data1;
            end
            if (ready3) begin
                valid_slots[2] <= valid_slots[1];
                data3 <= data2;
            end
            if (ready4) begin
                valid_slots[3] <= valid_slots[2];
                data4 <= data3;
            end
            if (ready5) begin
                valid_slots[4] <= valid_slots[3];
                data5 <= data4;
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
