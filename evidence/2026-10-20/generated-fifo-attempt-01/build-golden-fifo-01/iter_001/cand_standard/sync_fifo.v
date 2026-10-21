`timescale 1ns/1ps
module sync_fifo (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    sync_fifo_core #(
        .WIDTH(8),
        .DEPTH(3)
    ) u_sync_fifo_core (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(out_data),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule

module sync_fifo_core #(
    parameter WIDTH = 8,
    parameter DEPTH = 3
) (
    input wire clk,
    input wire rst,
    input wire [WIDTH-1:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [WIDTH-1:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    localparam PTR_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH);

    reg [WIDTH-1:0] mem [0:DEPTH-1];
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [PTR_WIDTH-1:0] rd_ptr;
    reg wr_phase;
    reg rd_phase;

    wire empty;
    wire full;
    wire push;
    wire pop;

    assign empty = (wr_ptr == rd_ptr) && (wr_phase == rd_phase);
    assign full = (wr_ptr == rd_ptr) && (wr_phase != rd_phase);

    assign out_valid = !empty;
    assign pop = out_valid && out_ready;
    assign in_ready = !full || pop;
    assign push = in_valid && in_ready;
    assign out_data = mem[rd_ptr];

    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= {PTR_WIDTH{1'b0}};
            rd_ptr <= {PTR_WIDTH{1'b0}};
            wr_phase <= 1'b0;
            rd_phase <= 1'b0;
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                if (wr_ptr == DEPTH - 1) begin
                    wr_ptr <= {PTR_WIDTH{1'b0}};
                    wr_phase <= ~wr_phase;
                end else begin
                    wr_ptr <= wr_ptr + 1'b1;
                end
            end

            if (pop) begin
                if (rd_ptr == DEPTH - 1) begin
                    rd_ptr <= {PTR_WIDTH{1'b0}};
                    rd_phase <= ~rd_phase;
                end else begin
                    rd_ptr <= rd_ptr + 1'b1;
                end
            end
        end
    end
endmodule