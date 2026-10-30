`timescale 1ns/1ps
// Qualification reference only: rr_regfile_tb.v must pass this source and
// fail every mutant in mutants.json. Never configured as a generation seed.
// The top below is byte-identical to the harness's mechanical wrapper.
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
    output reg [3:0] grant,
    output reg wr_en,
    output reg [2:0] wr_addr,
    output reg [7:0] wr_data
);
    reg [1:0] last;       // most recently granted requester
    reg [1:0] winner;
    reg [1:0] candidate;
    reg found;
    integer offset;

    // Search last+1, last+2, last+3, last (mod 4); the first requester wins.
    always @(*) begin
        found = 1'b0;
        winner = 2'd0;
        candidate = 2'd0;
        for (offset = 1; offset <= 4; offset = offset + 1) begin
            candidate = last + offset;
            if (!found && req[candidate]) begin
                found = 1'b1;
                winner = candidate;
            end
        end
    end

    wire [2:0] selected_addr = (winner == 2'd0) ? addr0 : (winner == 2'd1) ? addr1 :
                               (winner == 2'd2) ? addr2 : addr3;
    wire [7:0] selected_data = (winner == 2'd0) ? data0 : (winner == 2'd1) ? data1 :
                               (winner == 2'd2) ? data2 : data3;

    always @(posedge clk) begin // arbiter_clock
        if (rst) begin
            last <= 2'd3; // reset_pointer
            grant <= 4'd0;
            wr_en <= 1'b0;
            wr_addr <= 3'd0;
            wr_data <= 8'd0;
        end else if (found) begin
            last <= winner; // rotate
            grant <= 4'd1 << winner;
            wr_en <= 1'b1;
            wr_addr <= selected_addr;
            wr_data <= selected_data;
        end else begin
            grant <= 4'd0;
            wr_en <= 1'b0;
            wr_addr <= 3'd0;
            wr_data <= 8'd0;
        end
    end
endmodule

// @latency 1
module regfile8x8 (
    input wire clk,
    input wire rst,
    input wire wr_en,
    input wire [2:0] wr_addr,
    input wire [7:0] wr_data,
    input wire [2:0] rd_addr,
    output reg [7:0] rd_data
);
    reg [7:0] mem [0:7];
    integer i;

    always @(posedge clk) begin // regfile_clock
        if (rst) begin
            for (i = 0; i < 8; i = i + 1)
                mem[i] <= mem[i]; // clear_memory
            rd_data <= 8'd0;
        end else begin
            rd_data <= mem[rd_addr]; // read_first
            if (wr_en) mem[wr_addr] <= wr_data;
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
