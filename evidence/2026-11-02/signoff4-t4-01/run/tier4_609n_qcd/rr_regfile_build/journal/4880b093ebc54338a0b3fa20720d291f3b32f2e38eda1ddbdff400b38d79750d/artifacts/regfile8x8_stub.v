module regfile8x8 (
    input wire clk,
    input wire rst,
    input wire wr_en,
    input wire [2:0] wr_addr,
    input wire [7:0] wr_data,
    input wire [2:0] rd_addr,
    output wire [7:0] rd_data
);
endmodule
