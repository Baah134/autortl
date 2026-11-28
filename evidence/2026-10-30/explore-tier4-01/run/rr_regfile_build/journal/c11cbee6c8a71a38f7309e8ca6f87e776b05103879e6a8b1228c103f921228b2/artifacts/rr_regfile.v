`timescale 1ns/1ps
module rr_regfile (
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
    input wire [2:0] rd_addr,
    output wire [3:0] grant,
    output wire [7:0] rd_data
);
    reg [1:0] last;
    reg [3:0] grant_reg;
    reg wr_en_reg;
    reg [2:0] wr_addr_reg;
    reg [7:0] wr_data_reg;
    reg found;
    reg [1:0] winner;

    wire [3:0] w_grant;
    wire w_wr_en;
    wire [2:0] w_wr_addr;
    wire [7:0] w_wr_data;

    assign grant = grant_reg;
    assign w_grant = grant_reg;
    assign w_wr_en = wr_en_reg;
    assign w_wr_addr = wr_addr_reg;
    assign w_wr_data = wr_data_reg;

    always @(*) begin
        found = 1'b0;
        winner = 2'd0;

        case (last)
            2'd0: begin
                if (req[1]) begin
                    found = 1'b1;
                    winner = 2'd1;
                end else if (req[2]) begin
                    found = 1'b1;
                    winner = 2'd2;
                end else if (req[3]) begin
                    found = 1'b1;
                    winner = 2'd3;
                end else if (req[0]) begin
                    found = 1'b1;
                    winner = 2'd0;
                end
            end
            2'd1: begin
                if (req[2]) begin
                    found = 1'b1;
                    winner = 2'd2;
                end else if (req[3]) begin
                    found = 1'b1;
                    winner = 2'd3;
                end else if (req[0]) begin
                    found = 1'b1;
                    winner = 2'd0;
                end else if (req[1]) begin
                    found = 1'b1;
                    winner = 2'd1;
                end
            end
            2'd2: begin
                if (req[3]) begin
                    found = 1'b1;
                    winner = 2'd3;
                end else if (req[0]) begin
                    found = 1'b1;
                    winner = 2'd0;
                end else if (req[1]) begin
                    found = 1'b1;
                    winner = 2'd1;
                end else if (req[2]) begin
                    found = 1'b1;
                    winner = 2'd2;
                end
            end
            default: begin
                if (req[0]) begin
                    found = 1'b1;
                    winner = 2'd0;
                end else if (req[1]) begin
                    found = 1'b1;
                    winner = 2'd1;
                end else if (req[2]) begin
                    found = 1'b1;
                    winner = 2'd2;
                end else if (req[3]) begin
                    found = 1'b1;
                    winner = 2'd3;
                end
            end
        endcase
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
            case (winner)
                2'd0: begin
                    grant_reg <= 4'b0001;
                    wr_addr_reg <= addr0;
                    wr_data_reg <= data0;
                end
                2'd1: begin
                    grant_reg <= 4'b0010;
                    wr_addr_reg <= addr1;
                    wr_data_reg <= data1;
                end
                2'd2: begin
                    grant_reg <= 4'b0100;
                    wr_addr_reg <= addr2;
                    wr_data_reg <= data2;
                end
                default: begin
                    grant_reg <= 4'b1000;
                    wr_addr_reg <= addr3;
                    wr_data_reg <= data3;
                end
            endcase
            wr_en_reg <= 1'b1;
        end else begin
            grant_reg <= 4'b0000;
            wr_en_reg <= 1'b0;
            wr_addr_reg <= 3'b000;
            wr_data_reg <= 8'b00000000;
        end
    end

    regfile8x8 u_regfile8x8 (
        .clk(clk),
        .rst(rst),
        .wr_en(w_wr_en),
        .wr_addr(w_wr_addr),
        .wr_data(w_wr_data),
        .rd_addr(rd_addr),
        .rd_data(rd_data)
    );
endmodule