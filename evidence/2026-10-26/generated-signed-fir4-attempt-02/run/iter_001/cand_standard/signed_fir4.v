`timescale 1ns/1ps
// @latency 3
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
    reg signed [7:0] x1;
    reg signed [7:0] x2;
    reg signed [7:0] x3;

    reg v1;
    reg v2;
    reg v3;

    reg signed [12:0] d1;
    reg signed [12:0] d2;
    reg signed [12:0] d3;

    reg [1:0] occupancy;
    reg [1:0] occupancy_next;
    reg full;

    wire r3 = !v3 || out_ready;
    wire r2 = !v2 || r3;
    wire accepted = in_valid && in_ready;
    wire retired = v3 && out_ready;

    assign in_ready = !full || out_ready;
    assign out_valid = v3;
    assign out_data = d3;

    wire signed [12:0] x_ext  = {{5{x[7]}}, x};
    wire signed [12:0] x1_ext = {{5{x1[7]}}, x1};
    wire signed [12:0] x2_ext = {{5{x2[7]}}, x2};
    wire signed [12:0] x3_ext = {{5{x3[7]}}, x3};

    wire signed [12:0] fir_value =
        (x_ext  * 13'sd3) +
        (x1_ext * -13'sd5) +
        (x2_ext * 13'sd7) -
        (x3_ext * 13'sd2);

    always @(*) begin
        occupancy_next = occupancy;
        case ({accepted, retired})
            2'b10: occupancy_next = occupancy + 2'd1;
            2'b01: occupancy_next = occupancy - 2'd1;
            default: occupancy_next = occupancy;
        endcase
    end

    always @(posedge clk) begin
        if (rst) begin
            x1 <= 8'sd0;
            x2 <= 8'sd0;
            x3 <= 8'sd0;
            v1 <= 1'b0;
            v2 <= 1'b0;
            v3 <= 1'b0;
            occupancy <= 2'd0;
            full <= 1'b0;
        end else begin
            occupancy <= occupancy_next;
            full <= (occupancy_next == 2'd3);

            if (r3) begin
                v3 <= v2;
                if (v2)
                    d3 <= d2;
            end

            if (r2) begin
                v2 <= v1;
                if (v1)
                    d2 <= d1;
            end

            if (in_ready) begin
                v1 <= in_valid;
                if (in_valid)
                    d1 <= fir_value;
            end

            if (accepted) begin
                x3 <= x2;
                x2 <= x1;
                x1 <= x;
            end
        end
    end
endmodule