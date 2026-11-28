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

    reg v1, v2, v3, v4, v5;
    reg signed [15:0] history [0:14];
    reg signed [16:0] pair1 [0:7];

    reg signed [19:0] p0_reg;
    reg signed [21:0] p1_reg, p2_reg, p3_reg;
    reg signed [23:0] p4_reg;
    reg signed [24:0] p5_reg;
    reg signed [25:0] p6_reg, p7_reg;
    reg signed [23:0] acc3_lo;
    reg signed [27:0] acc3_hi;
    reg signed [16:0] rounded4;
    reg signed [15:0] d5;

    wire ready5 = !v5 || out_ready;
    wire ready4 = !v4 || ready5;
    wire ready3 = !v3 || ready4;
    wire ready2 = !v2 || ready3;
    wire ready1 = !v1 || ready2;

    assign in_ready = ready1;
    assign out_valid = v5;
    assign out_sample = d5;

    wire signed [19:0] p0 =
        $signed({{3{pair1[0][16]}}, pair1[0]}) * -20'sd6;
    wire signed [21:0] p1 =
        $signed({{5{pair1[1][16]}}, pair1[1]}) * -22'sd20;
    wire signed [21:0] p2 =
        $signed({{5{pair1[2][16]}}, pair1[2]}) * -22'sd24;
    wire signed [21:0] p3 =
        $signed({{5{pair1[3][16]}}, pair1[3]}) * 22'sd18;
    wire signed [23:0] p4 =
        $signed({{7{pair1[4][16]}}, pair1[4]}) * 24'sd110;
    wire signed [24:0] p5 =
        $signed({{8{pair1[5][16]}}, pair1[5]}) * 25'sd226;
    wire signed [25:0] p6 =
        $signed({{9{pair1[6][16]}}, pair1[6]}) * 26'sd330;
    wire signed [25:0] p7 =
        $signed({{9{pair1[7][16]}}, pair1[7]}) * 26'sd390;

    wire signed [21:0] sum01 =
        $signed({{2{p0_reg[19]}}, p0_reg}) +
        $signed({{0{p1_reg[21]}}, p1_reg});
    wire signed [22:0] sum23 =
        $signed({p2_reg[21], p2_reg}) +
        $signed({p3_reg[21], p3_reg});
    wire signed [25:0] sum45 =
        $signed({{2{p4_reg[23]}}, p4_reg}) +
        $signed({p5_reg[24], p5_reg});
    wire signed [26:0] sum67 =
        $signed({p6_reg[25], p6_reg}) +
        $signed({p7_reg[25], p7_reg});

    wire signed [23:0] sum0123 =
        $signed({{2{sum01[21]}}, sum01}) +
        $signed({sum23[22], sum23});
    wire signed [27:0] sum4567 =
        $signed({{2{sum45[25]}}, sum45}) +
        $signed({sum67[26], sum67});

    wire signed [27:0] total_acc =
        $signed({{4{acc3_lo[23]}}, acc3_lo}) + acc3_hi;
    wire signed [16:0] rounded_value =
        (total_acc + 28'sd1024) >>> 11;
    wire signed [15:0] result5 =
        (rounded4[16] != rounded4[15]) ?
            (rounded4[16] ? -16'sd32768 : 16'sd32767) :
            rounded4[15:0];

    integer j;
    always @(posedge clk) begin
        if (rst) begin
            v1 <= 1'b0;
            v2 <= 1'b0;
            v3 <= 1'b0;
            v4 <= 1'b0;
            v5 <= 1'b0;
            for (j = 0; j < 15; j = j + 1)
                history[j] <= 16'sd0;
        end else begin
            if (ready1) begin
                v1 <= in_valid;
                if (in_valid) begin
                    pair1[0] <= {in_sample[15], in_sample} +
                                {history[14][15], history[14]};
                    pair1[1] <= {history[0][15], history[0]} +
                                {history[13][15], history[13]};
                    pair1[2] <= {history[1][15], history[1]} +
                                {history[12][15], history[12]};
                    pair1[3] <= {history[2][15], history[2]} +
                                {history[11][15], history[11]};
                    pair1[4] <= {history[3][15], history[3]} +
                                {history[10][15], history[10]};
                    pair1[5] <= {history[4][15], history[4]} +
                                {history[9][15], history[9]};
                    pair1[6] <= {history[5][15], history[5]} +
                                {history[8][15], history[8]};
                    pair1[7] <= {history[6][15], history[6]} +
                                {history[7][15], history[7]};
                    for (j = 14; j > 0; j = j - 1)
                        history[j] <= history[j-1];
                    history[0] <= in_sample;
                end
            end

            if (ready2) begin
                v2 <= v1;
                if (v1) begin
                    p0_reg <= p0;
                    p1_reg <= p1;
                    p2_reg <= p2;
                    p3_reg <= p3;
                    p4_reg <= p4;
                    p5_reg <= p5;
                    p6_reg <= p6;
                    p7_reg <= p7;
                end
            end

            if (ready3) begin
                v3 <= v2;
                if (v2) begin
                    acc3_lo <= sum0123;
                    acc3_hi <= sum4567;
                end
            end

            if (ready4) begin
                v4 <= v3;
                if (v3)
                    rounded4 <= rounded_value;
            end

            if (ready5) begin
                v5 <= v4;
                if (v4)
                    d5 <= result5;
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