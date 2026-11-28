`timescale 1ns/1ps
// @latency 1
module skid_buffer (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    reg [7:0] head_data;
    reg [7:0] tail_data;
    reg head_valid;
    reg tail_valid;

    wire push;
    wire pop;

    assign out_valid = head_valid || tail_valid;
    assign in_ready = !(head_valid && tail_valid) || out_ready;
    assign out_data = head_data;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            head_valid <= 1'b0;
            tail_valid <= 1'b0;
        end else if (!head_valid) begin
            if (push) begin
                head_data <= in_data;
                head_valid <= 1'b1;
            end
        end else if (!tail_valid) begin
            if (push && pop) begin
                head_data <= in_data;
            end else if (push) begin
                tail_data <= in_data;
                tail_valid <= 1'b1;
            end else if (pop) begin
                head_valid <= 1'b0;
            end
        end else if (pop) begin
            head_data <= tail_data;
            if (push) begin
                tail_data <= in_data;
            end else begin
                tail_valid <= 1'b0;
            end
        end
    end
endmodule