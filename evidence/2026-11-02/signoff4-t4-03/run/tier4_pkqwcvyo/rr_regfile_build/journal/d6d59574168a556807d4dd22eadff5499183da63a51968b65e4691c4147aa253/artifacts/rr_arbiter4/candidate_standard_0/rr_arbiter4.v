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
    reg [1:0] winner;
    reg found;

    reg [3:0] grant_reg;
    reg wr_en_reg;
    reg [2:0] wr_addr_reg;
    reg [7:0] wr_data_reg;

    assign grant = grant_reg;
    assign wr_en = wr_en_reg;
    assign wr_addr = wr_addr_reg;
    assign wr_data = wr_data_reg;

    always @(*) begin
        winner = 2'd0;
        found = 1'b0;

        case (last)
            2'd0: begin
                if (req[1]) begin winner = 2'd1; found = 1'b1; end
                else if (req[2]) begin winner = 2'd2; found = 1'b1; end
                else if (req[3]) begin winner = 2'd3; found = 1'b1; end
                else if (req[0]) begin winner = 2'd0; found = 1'b1; end
            end
            2'd1: begin
                if (req[2]) begin winner = 2'd2; found = 1'b1; end
                else if (req[3]) begin winner = 2'd3; found = 1'b1; end
                else if (req[0]) begin winner = 2'd0; found = 1'b1; end
                else if (req[1]) begin winner = 2'd1; found = 1'b1; end
            end
            2'd2: begin
                if (req[3]) begin winner = 2'd3; found = 1'b1; end
                else if (req[0]) begin winner = 2'd0; found = 1'b1; end
                else if (req[1]) begin winner = 2'd1; found = 1'b1; end
                else if (req[2]) begin winner = 2'd2; found = 1'b1; end
            end
            default: begin
                if (req[0]) begin winner = 2'd0; found = 1'b1; end
                else if (req[1]) begin winner = 2'd1; found = 1'b1; end
                else if (req[2]) begin winner = 2'd2; found = 1'b1; end
                else if (req[3]) begin winner = 2'd3; found = 1'b1; end
            end
        endcase
    end

    always @(posedge clk) begin
        if (rst) begin
            grant_reg <= 4'b0000;
            wr_en_reg <= 1'b0;
            wr_addr_reg <= 3'b000;
            wr_data_reg <= 8'b00000000;
            last <= 2'd3;
        end else if (found) begin
            grant_reg <= 4'b0001 << winner;
            wr_en_reg <= 1'b1;
            last <= winner;

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