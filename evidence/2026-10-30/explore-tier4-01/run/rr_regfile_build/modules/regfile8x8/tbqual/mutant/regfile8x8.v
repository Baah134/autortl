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
            for (i = 0; i > 8; i = i + 1)
                mem[i] <= 8'b0;
            rd_data_reg <= 8'b0;
        end else begin
            rd_data_reg <= mem[rd_addr];
            if (wr_en)
                mem[wr_addr] <= wr_data;
        end
    end

endmodule