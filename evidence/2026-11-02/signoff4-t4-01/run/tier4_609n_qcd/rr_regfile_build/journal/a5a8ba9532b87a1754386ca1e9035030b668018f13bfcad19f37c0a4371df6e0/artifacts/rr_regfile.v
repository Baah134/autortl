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

    reg [3:0] winner;
    wire found;
    wire [2:0] addr_mux;
    wire [7:0] data_mux;

    assign grant = grant_reg;
    assign wr_en = wr_en_reg;
    assign wr_addr = wr_addr_reg;
    assign wr_data = wr_data_reg;
    assign found = |winner;

    assign addr_mux =
        ({3{winner[0]}} & addr0) |
        ({3{winner[1]}} & addr1) |
        ({3{winner[2]}} & addr2) |
        ({3{winner[3]}} & addr3);

    assign data_mux =
        ({8{winner[0]}} & data0) |
        ({8{winner[1]}} & data1) |
        ({8{winner[2]}} & data2) |
        ({8{winner[3]}} & data3);

    always @(*) begin
        winner = 4'b0000;
        case (last)
            2'd0: begin
                winner[0] = req[0] & ~req[1] & ~req[2] & ~req[3];
                winner[1] = req[1];
                winner[2] = req[2] & ~req[1];
                winner[3] = req[3] & ~req[1] & ~req[2];
            end
            2'd1: begin
                winner[0] = req[0] & ~req[2] & ~req[3];
                winner[1] = req[1] & ~req[2] & ~req[3] & ~req[0];
                winner[2] = req[2];
                winner[3] = req[3] & ~req[2];
            end
            2'd2: begin
                winner[0] = req[0] & ~req[3];
                winner[1] = req[1] & ~req[3] & ~req[0];
                winner[2] = req[2] & ~req[3] & ~req[0] & ~req[1];
                winner[3] = req[3];
            end
            default: begin
                winner[0] = req[0];
                winner[1] = req[1] & ~req[0];
                winner[2] = req[2] & ~req[0] & ~req[1];
                winner[3] = req[3] & ~req[0] & ~req[1] & ~req[2];
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
        end else begin
            grant_reg <= winner;
            wr_en_reg <= found;
            wr_addr_reg <= addr_mux;
            wr_data_reg <= data_mux;
            if (found)
                last <= {winner[3] | winner[2], winner[3] | winner[1]};
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
module regfile8x8 (
    input wire clk,
    input wire rst,
    input wire wr_en,
    input wire [2:0] wr_addr,
    input wire [7:0] wr_data,
    input wire [2:0] rd_addr,
    output wire [7:0] rd_data
);

    reg [7:0] mem [0:7];
    reg [7:0] rd_data_reg;
    integer i;

    assign rd_data = rd_data_reg;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                mem[i] <= 8'b0;
            rd_data_reg <= 8'b0;
        end else begin
            rd_data_reg <= mem[rd_addr];
            if (wr_en)
                mem[wr_addr] <= wr_data;
        end
    end

endmodule

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

    wire w_rr_arbiter4_wr_en;
    wire [2:0] w_rr_arbiter4_wr_addr;
    wire [7:0] w_rr_arbiter4_wr_data;

    rr_arbiter4 u_rr_arbiter4 (
        .clk(clk),
        .rst(rst),
        .req(req),
        .addr0(addr0),
        .data0(data0),
        .addr1(addr1),
        .data1(data1),
        .addr2(addr2),
        .data2(data2),
        .addr3(addr3),
        .data3(data3),
        .grant(grant),
        .wr_en(w_rr_arbiter4_wr_en),
        .wr_addr(w_rr_arbiter4_wr_addr),
        .wr_data(w_rr_arbiter4_wr_data)
    );

    regfile8x8 u_regfile8x8 (
        .clk(clk),
        .rst(rst),
        .wr_en(w_rr_arbiter4_wr_en),
        .wr_addr(w_rr_arbiter4_wr_addr),
        .wr_data(w_rr_arbiter4_wr_data),
        .rd_addr(rd_addr),
        .rd_data(rd_data)
    );

endmodule