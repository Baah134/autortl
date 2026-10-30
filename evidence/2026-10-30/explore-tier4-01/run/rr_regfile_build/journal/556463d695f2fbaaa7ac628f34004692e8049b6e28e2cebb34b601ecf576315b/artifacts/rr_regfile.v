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

    reg [7:0] mem [0:7];
    reg [7:0] rd_data_reg;
    integer i;

    wire [7:0] rd_sel0;
    wire [7:0] rd_sel1;
    wire [7:0] rd_sel2;
    wire [7:0] rd_sel3;
    wire [7:0] rd_sel4;
    wire [7:0] rd_sel5;
    wire [7:0] rd_sel6;
    wire [7:0] rd_sel7;

    wire [7:0] rd_term0;
    wire [7:0] rd_term1;
    wire [7:0] rd_term2;
    wire [7:0] rd_term3;
    wire [7:0] rd_term4;
    wire [7:0] rd_term5;
    wire [7:0] rd_term6;
    wire [7:0] rd_term7;

    wire [7:0] rd_pair0;
    wire [7:0] rd_pair1;
    wire [7:0] rd_pair2;
    wire [7:0] rd_pair3;
    wire [7:0] rd_half0;
    wire [7:0] rd_half1;
    wire [7:0] rd_mux;

    assign rd_sel0 = (rd_addr == 3'd0);
    assign rd_sel1 = (rd_addr == 3'd1);
    assign rd_sel2 = (rd_addr == 3'd2);
    assign rd_sel3 = (rd_addr == 3'd3);
    assign rd_sel4 = (rd_addr == 3'd4);
    assign rd_sel5 = (rd_addr == 3'd5);
    assign rd_sel6 = (rd_addr == 3'd6);
    assign rd_sel7 = (rd_addr == 3'd7);

    assign rd_term0 = mem[0] & {8{rd_sel0[0]}};
    assign rd_term1 = mem[1] & {8{rd_sel1[0]}};
    assign rd_term2 = mem[2] & {8{rd_sel2[0]}};
    assign rd_term3 = mem[3] & {8{rd_sel3[0]}};
    assign rd_term4 = mem[4] & {8{rd_sel4[0]}};
    assign rd_term5 = mem[5] & {8{rd_sel5[0]}};
    assign rd_term6 = mem[6] & {8{rd_sel6[0]}};
    assign rd_term7 = mem[7] & {8{rd_sel7[0]}};

    assign rd_pair0 = rd_term0 | rd_term1;
    assign rd_pair1 = rd_term2 | rd_term3;
    assign rd_pair2 = rd_term4 | rd_term5;
    assign rd_pair3 = rd_term6 | rd_term7;
    assign rd_half0 = rd_pair0 | rd_pair1;
    assign rd_half1 = rd_pair2 | rd_pair3;
    assign rd_mux = rd_half0 | rd_half1;

    assign rd_data = rd_data_reg;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                mem[i] <= 8'b0;
            rd_data_reg <= 8'b0;
        end else begin
            rd_data_reg <= rd_mux;
            if (w_rr_arbiter4_wr_en)
                mem[w_rr_arbiter4_wr_addr] <= w_rr_arbiter4_wr_data;
        end
    end
endmodule