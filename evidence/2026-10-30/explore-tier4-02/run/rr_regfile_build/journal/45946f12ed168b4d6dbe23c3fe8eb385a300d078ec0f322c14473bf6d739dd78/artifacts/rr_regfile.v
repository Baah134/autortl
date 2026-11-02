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

    reg [3:0] last_ptr;
    reg [3:0] grant_reg;
    reg wr_en_reg;
    reg [2:0] wr_addr_reg;
    reg [7:0] wr_data_reg;
    wire [3:0] winner;
    wire [2:0] addr_sel;
    wire [7:0] data_sel;

    assign winner[0] = req[0] &
        ((last_ptr[3]) |
         (last_ptr[0] & ~req[1] & ~req[2] & ~req[3]) |
         (last_ptr[1] & ~req[2] & ~req[3]) |
         (last_ptr[2] & ~req[3]));

    assign winner[1] = req[1] &
        ((last_ptr[0]) |
         (last_ptr[1] & ~req[2] & ~req[3] & ~req[0]) |
         (last_ptr[2] & ~req[3] & ~req[0]) |
         (last_ptr[3] & ~req[0]));

    assign winner[2] = req[2] &
        ((last_ptr[1]) |
         (last_ptr[2] & ~req[3] & ~req[0] & ~req[1]) |
         (last_ptr[3] & ~req[0] & ~req[1]) |
         (last_ptr[0] & ~req[1]));

    assign winner[3] = req[3] &
        ((last_ptr[2]) |
         (last_ptr[3] & ~req[0] & ~req[1] & ~req[2]) |
         (last_ptr[0] & ~req[1] & ~req[2]) |
         (last_ptr[1] & ~req[2]));

    assign addr_sel = ({3{winner[0]}} & addr0) |
                      ({3{winner[1]}} & addr1) |
                      ({3{winner[2]}} & addr2) |
                      ({3{winner[3]}} & addr3);

    assign data_sel = ({8{winner[0]}} & data0) |
                      ({8{winner[1]}} & data1) |
                      ({8{winner[2]}} & data2) |
                      ({8{winner[3]}} & data3);

    assign grant = grant_reg;
    assign wr_en = wr_en_reg;
    assign wr_addr = wr_addr_reg;
    assign wr_data = wr_data_reg;

    always @(posedge clk) begin
        if (rst) begin
            last_ptr <= 4'b1000;
            grant_reg <= 4'b0000;
            wr_en_reg <= 1'b0;
            wr_addr_reg <= 3'b000;
            wr_data_reg <= 8'b00000000;
        end else if (|winner) begin
            last_ptr <= winner;
            grant_reg <= winner;
            wr_en_reg <= 1'b1;
            wr_addr_reg <= addr_sel;
            wr_data_reg <= data_sel;
        end else begin
            grant_reg <= 4'b0000;
            wr_en_reg <= 1'b0;
            wr_addr_reg <= 3'b000;
            wr_data_reg <= 8'b00000000;
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
    reg [7:0] rd_data_q;
    integer i;

    assign rd_data = rd_data_q;

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                mem[i] <= 8'b0;
            rd_data_q <= 8'b0;
        end else begin
            rd_data_q <= mem[rd_addr];
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