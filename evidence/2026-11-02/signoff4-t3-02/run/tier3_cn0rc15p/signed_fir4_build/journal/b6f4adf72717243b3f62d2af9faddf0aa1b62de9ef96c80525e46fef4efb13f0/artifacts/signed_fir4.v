`timescale 1ns/1ps
// @latency 3
module signed_fir4_core (
    input wire clk,
    input wire rst,
    input wire signed [7:0] x,
    input wire in_valid,
    output wire in_ready,
    output wire signed [12:0] out_data,
    output wire out_valid,
    input wire out_ready
);

    reg v1, v2, v3;
    reg vacancy;
    reg signed [12:0] data1, data2, data3;
    reg signed [7:0] hist1, hist2, hist3;

    wire r3 = !v3 || out_ready;
    wire r2 = !v2 || r3;
    wire r1 = vacancy || out_ready;

    wire v1_next = r1 ? in_valid : v1;
    wire v2_next = r2 ? v1 : v2;
    wire v3_next = r3 ? v2 : v3;
    wire vacancy_next = !(v1_next && v2_next && v3_next);

    assign in_ready = r1;
    assign out_valid = v3;
    assign out_data = data3;

    wire signed [12:0] x_ext  = {{5{x[7]}}, x};
    wire signed [12:0] h1_ext = {{5{hist1[7]}}, hist1};
    wire signed [12:0] h2_ext = {{5{hist2[7]}}, hist2};
    wire signed [12:0] h3_ext = {{5{hist3[7]}}, hist3};

    wire signed [12:0] term0 = x_ext + (x_ext <<< 1);
    wire signed [12:0] term1 = h1_ext + (h1_ext <<< 2);
    wire signed [12:0] term2 = h2_ext + (h2_ext <<< 1) + (h2_ext <<< 2);
    wire signed [12:0] term3 = h3_ext <<< 1;

    wire signed [12:0] pair01 = term0 - term1;
    wire signed [12:0] pair23 = term2 - term3;
    wire signed [12:0] fir_result = pair01 + pair23;

    always @(posedge clk) begin
        if (rst) begin
            hist1 <= 8'sd0;
            hist2 <= 8'sd0;
            hist3 <= 8'sd0;
            v1 <= 1'b0;
            v2 <= 1'b0;
            v3 <= 1'b0;
            vacancy <= 1'b1;
        end else begin
            vacancy <= vacancy_next;
            v1 <= v1_next;
            v2 <= v2_next;
            v3 <= v3_next;

            if (in_valid && in_ready) begin
                hist3 <= hist2;
                hist2 <= hist1;
                hist1 <= x;
            end

            if (r1 && in_valid)
                data1 <= fir_result;

            if (r2 && v1)
                data2 <= data1;

            if (r3 && v2)
                data3 <= data2;
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 3
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
module signed_fir4 (
    input wire clk,
    input wire rst,
    input wire signed [7:0] x,
    input wire in_valid,
    output wire in_ready,
    output wire signed [12:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    signed_fir4_core u_signed_fir4_core (
        .clk(clk),
        .rst(rst),
        .x(x),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule