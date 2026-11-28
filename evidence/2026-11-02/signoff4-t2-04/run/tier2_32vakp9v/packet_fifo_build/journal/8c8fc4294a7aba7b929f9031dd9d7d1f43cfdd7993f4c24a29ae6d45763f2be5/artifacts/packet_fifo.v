`timescale 1ns/1ps
// @latency 1
module packet_fifo_core #(
    parameter WIDTH = 8,
    parameter DEPTH = 3
) (
    input wire clk,
    input wire rst,
    input wire [WIDTH-1:0] in_data,
    input wire in_last,
    input wire in_valid,
    output wire in_ready,
    output wire [WIDTH-1:0] out_data,
    output wire out_last,
    output wire out_valid,
    input wire out_ready
);

    localparam PTR_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH);
    localparam COUNT_WIDTH = $clog2(DEPTH + 1);

    reg [WIDTH-1:0] data_mem [0:DEPTH-1];
    reg last_mem [0:DEPTH-1];
    reg [PTR_WIDTH-1:0] rd_ptr;
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [COUNT_WIDTH-1:0] occupancy;
    reg has_space;
    reg valid_reg;
    reg [WIDTH-1:0] head_data;
    reg head_last;

    wire push;
    wire pop;
    wire [PTR_WIDTH-1:0] next_rd_ptr;

    assign out_valid = valid_reg;
    assign in_ready = has_space || out_ready;
    assign out_data = head_data;
    assign out_last = head_last;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;
    assign next_rd_ptr = (rd_ptr == DEPTH - 1) ? {PTR_WIDTH{1'b0}} :
                         rd_ptr + 1'b1;

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= 0;
            wr_ptr <= 0;
            occupancy <= 0;
            has_space <= 1'b1;
            valid_reg <= 1'b0;
            head_data <= 0;
            head_last <= 0;
        end else begin
            if (push) begin
                data_mem[wr_ptr] <= in_data;
                last_mem[wr_ptr] <= in_last;
                if (wr_ptr == DEPTH - 1)
                    wr_ptr <= 0;
                else
                    wr_ptr <= wr_ptr + 1'b1;
            end

            if (pop) begin
                rd_ptr <= next_rd_ptr;
                if (occupancy == 1) begin
                    if (push) begin
                        head_data <= in_data;
                        head_last <= in_last;
                    end
                end else begin
                    head_data <= data_mem[next_rd_ptr];
                    head_last <= last_mem[next_rd_ptr];
                end
            end else if (push && (occupancy == 0)) begin
                head_data <= in_data;
                head_last <= in_last;
            end

            case ({push, pop})
                2'b10: begin
                    occupancy <= occupancy + 1'b1;
                    has_space <= (occupancy < DEPTH - 1);
                    valid_reg <= 1'b1;
                end
                2'b01: begin
                    occupancy <= occupancy - 1'b1;
                    has_space <= 1'b1;
                    valid_reg <= (occupancy > 1);
                end
                2'b11: begin
                    occupancy <= occupancy;
                    has_space <= has_space;
                    valid_reg <= 1'b1;
                end
                default: begin
                    occupancy <= occupancy;
                    has_space <= has_space;
                    valid_reg <= valid_reg;
                end
            endcase
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
module packet_fifo (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_last,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_last,
    output wire out_valid,
    input wire out_ready
);
    packet_fifo_core #(.WIDTH(8), .DEPTH(3)) u_packet_fifo_core (
        .clk(clk),
        .rst(rst),
        .in_data(in_data),
        .in_last(in_last),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .out_data(out_data),
        .out_last(out_last),
        .out_valid(out_valid),
        .out_ready(out_ready)
    );
endmodule