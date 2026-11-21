`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire        clk,
    input  wire        load,
    input  wire        ena,
    input  wire [1:0]  amount,
    input  wire [63:0] data,
    output wire [63:0] q
);

    reg  [63:0] q_reg;
    reg  [63:0] shifted;
    wire        update_en;
    wire [63:0] next_q;

    always @(*) begin
        shifted = {q_reg[62:0], 1'b0};
        case (amount)
            2'd0: shifted = {q_reg[62:0], 1'b0};
            2'd1: shifted = {q_reg[55:0], 8'b0};
            2'd2: shifted = {q_reg[63], q_reg[63:1]};
            2'd3: shifted = {{8{q_reg[63]}}, q_reg[63:8]};
        endcase
    end

    assign update_en = load | ena;
    assign next_q = load ? data : shifted;
    assign q = q_reg;

    always @(posedge clk) begin
        if (update_en)
            q_reg <= next_q;
    end

endmodule