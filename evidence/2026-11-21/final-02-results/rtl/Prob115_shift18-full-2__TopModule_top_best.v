`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input wire clk,
    input wire load,
    input wire ena,
    input wire [1:0] amount,
    input wire [63:0] data,
    output wire [63:0] q
);
    reg [55:0] q_high;
    reg [7:0] q_low;
    reg [55:0] shifted_high;
    reg [1:0] low_select;
    reg [7:0] next_low;

    wire update_en;
    wire clear_low;
    wire [55:0] next_high;

    assign q = {q_high, q_low};
    assign update_en = load | ena;
    assign clear_low = ena & ~load & (amount == 2'd1);
    assign next_high = load ? data[63:8] : shifted_high;

    always @(*) begin
        shifted_high = q[62:7];
        case (amount)
            2'd1: shifted_high = q[55:0];
            2'd2: shifted_high = {q[63], q[63:9]};
            2'd3: shifted_high = {{8{q[63]}}, q[63:16]};
        endcase
    end

    always @(*) begin
        low_select = 2'd0;
        if (load) begin
            low_select = 2'd1;
        end else begin
            case (amount)
                2'd2: low_select = 2'd2;
                2'd3: low_select = 2'd3;
            endcase
        end
    end

    always @(*) begin
        next_low = {q[6:0], 1'b0};
        case (low_select)
            2'd1: next_low = data[7:0];
            2'd2: next_low = q[8:1];
            2'd3: next_low = q[15:8];
        endcase
    end

    always @(posedge clk) begin
        if (update_en)
            q_high <= next_high;

        if (clear_low)
            q_low <= 8'b0;
        else if (update_en)
            q_low <= next_low;
    end
endmodule