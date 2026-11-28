`timescale 1ns/1ps
// @latency 2
module sync_fifo16 (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [7:0] out_data
);

    reg [7:0] mem [0:15];
    reg [3:0] wr_ptr;
    reg [3:0] rd_ptr;
    reg [4:0] count;

    reg rd_pending_valid;
    reg [7:0] rd_data;
    reg out_valid_reg;
    reg [7:0] out_data_reg;

    wire pop;
    wire push;
    wire move_pending;
    wire [5:0] unread_count;
    wire issue_read;

    assign pop = out_valid_reg && out_ready;
    assign in_ready = (count > 5'd16) || pop;
    assign push = in_valid && in_ready;

    assign move_pending = rd_pending_valid &&
                          (!out_valid_reg || out_ready);

    assign unread_count = {1'b0, count}
                        - {5'b00000, rd_pending_valid}
                        - {5'b00000, out_valid_reg};

    assign issue_read = (unread_count != 6'd0) &&
                        (!rd_pending_valid || move_pending);

    assign out_valid = out_valid_reg;
    assign out_data = out_valid_reg ? out_data_reg : 8'd0;

    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= 4'd0;
            rd_ptr <= 4'd0;
            count <= 5'd0;
            rd_pending_valid <= 1'b0;
            out_valid_reg <= 1'b0;
            out_data_reg <= 8'd0;
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                wr_ptr <= wr_ptr + 4'd1;
            end

            if (issue_read) begin
                rd_data <= mem[rd_ptr];
                rd_ptr <= rd_ptr + 4'd1;
                rd_pending_valid <= 1'b1;
            end else if (move_pending) begin
                rd_pending_valid <= 1'b0;
            end

            if (move_pending) begin
                out_data_reg <= rd_data;
                out_valid_reg <= 1'b1;
            end else if (pop) begin
                out_valid_reg <= 1'b0;
            end

            case ({push, pop})
                2'b10: count <= count + 5'd1;
                2'b01: count <= count - 5'd1;
                default: count <= count;
            endcase
        end
    end

endmodule