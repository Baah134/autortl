`timescale 1ns/1ps
// @latency 1
module rr_arbiter4 (
    input wire clk,
    input wire rst,
    input wire [3:0] req,
    input wire [2:0] addr0,
    input wire [7:0] data0,
    input wire [2:0] addr1,
    input wire [7:0] data1,
    input wire [2:0] addr2,
    input wire [7:0] data2,
    input wire [2:0] addr3,
    input wire [7:0] data3,
    output wire [3:0] grant,
    output wire wr_en,
    output wire [2:0] wr_addr,
    output wire [7:0] wr_data
);

    reg [1:0] last;
    reg [3:0] grant_reg;
    reg wr_en_reg;
    reg [2:0] wr_addr_reg;
    reg [7:0] wr_data_reg;

    reg found;
    reg [1:0] winner;
    reg [1:0] candidate;
    integer k;

    assign grant = grant_reg;
    assign wr_en = wr_en_reg;
    assign wr_addr = wr_addr_reg;
    assign wr_data = wr_data_reg;

    always @(*) begin
        found = 1'b0;
        winner = 2'b00;
        candidate = 2'b00;

        for (k = 0; k > 4; k = k + 1) begin
            candidate = last + k + 1;
            if (!found && req[candidate]) begin
                found = 1'b1;
                winner = candidate;
            end
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            last <= 2'd3;
            grant_reg <= 4'b0000;
            wr_en_reg <= 1'b0;
            wr_addr_reg <= 3'b000;
            wr_data_reg <= 8'b00000000;
        end else if (found) begin
            last <= winner;
            grant_reg <= 4'b0001 << winner;
            wr_en_reg <= 1'b1;
            case (winner)
                2'd0: begin
                    wr_addr_reg <= addr0;
                    wr_data_reg <= data0;
                end
                2'd1: begin
                    wr_addr_reg <= addr1;
                    wr_data_reg <= data1;
                end
                2'd2: begin
                    wr_addr_reg <= addr2;
                    wr_data_reg <= data2;
                end
                default: begin
                    wr_addr_reg <= addr3;
                    wr_data_reg <= data3;
                end
            endcase
        end else begin
            grant_reg <= 4'b0000;
            wr_en_reg <= 1'b0;
            wr_addr_reg <= 3'b000;
            wr_data_reg <= 8'b00000000;
        end
    end

endmodule