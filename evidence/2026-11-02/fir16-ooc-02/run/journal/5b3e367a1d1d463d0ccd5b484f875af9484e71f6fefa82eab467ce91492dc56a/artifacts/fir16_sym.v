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

    reg signed [24:0] p0_reg, p1_reg, p2_reg, p3_reg;
    reg signed [24:0] p4_reg, p5_reg, p6_reg, p7_reg;
    reg signed [26:0] acc3_lo, acc3_hi;
    reg signed [15:0] rounded4;
    reg signed [15:0] d5;

    wire ready5 = !v5 || out_ready;
    wire ready4 = !v4 || ready5;
    wire ready3 = !v3 || ready4;
    wire ready2 = !v2 || ready3;
    wire ready1 = !v1 || ready2;

    assign in_ready = ready1;
    assign out_valid = v5;
    assign out_sample = d5;

    wire signed [24:0] p0 = $signed(pair1[0]) * -25'sd3;
    wire signed [24:0] p1 = $signed(pair1[1]) * -25'sd10;
    wire signed [24:0] p2 = $signed(pair1[2]) * -25'sd12;
    wire signed [24:0] p3 = $signed(pair1[3]) * 25'sd9;
    wire signed [24:0] p4 = $signed(pair1[4]) * 25'sd55;
    wire signed [24:0] p5 = $signed(pair1[5]) * 25'sd113;
    wire signed [24:0] p6 = $signed(pair1[6]) * 25'sd165;
    wire signed [24:0] p7 = $signed(pair1[7]) * 25'sd195;

    wire signed [26:0] p0_ext = {{2{p0_reg[24]}}, p0_reg};
    wire signed [26:0] p1_ext = {{2{p1_reg[24]}}, p1_reg};
    wire signed [26:0] p2_ext = {{2{p2_reg[24]}}, p2_reg};
    wire signed [26:0] p3_ext = {{2{p3_reg[24]}}, p3_reg};
    wire signed [26:0] p4_ext = {{2{p4_reg[24]}}, p4_reg};
    wire signed [26:0] p5_ext = {{2{p5_reg[24]}}, p5_reg};
    wire signed [26:0] p6_ext = {{2{p6_reg[24]}}, p6_reg};
    wire signed [26:0] p7_ext = {{2{p7_reg[24]}}, p7_reg};

    wire signed [26:0] sum01 = p0_ext + p1_ext;
    wire signed [26:0] sum23 = p2_ext + p3_ext;
    wire signed [26:0] sum45 = p4_ext + p5_ext;
    wire signed [26:0] sum67 = p6_ext + p7_ext;
    wire signed [26:0] sum0123 = sum01 + sum23;
    wire signed [26:0] sum4567 = sum45 + sum67;

    wire signed [26:0] total_acc = acc3_lo + acc3_hi;
    wire signed [16:0] rounded_value =
        (total_acc + 27'sd512) >>> 10;
    wire signed [15:0] saturated_value =
        (rounded_value[16] != rounded_value[15]) ?
            (rounded_value[16] ? -16'sd32768 : 16'sd32767) :
            rounded_value[15:0];

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
                    rounded4 <= saturated_value;
            end

            if (ready5) begin
                v5 <= v4;
                if (v4)
                    d5 <= rounded4;
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