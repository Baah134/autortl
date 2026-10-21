`timescale 1ns/1ps
module skid_buffer (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    skid_buffer_core u_skid_buffer_core (
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

module skid_buffer_core (
    input wire clk,
    input wire rst,
    input wire [7:0] in_data,
    input wire in_valid,
    output wire in_ready,
    output wire [7:0] out_data,
    output wire out_valid,
    input wire out_ready
);
    reg nonempty;
    reg full;
    reg [7:0] data0;
    reg [7:0] data1;

    wire push;
    wire pop;

    assign in_ready = ~full;
    assign out_valid = nonempty;
    assign out_data = data0;

    assign push = in_valid & in_ready;
    assign pop = out_valid & out_ready;

    always @(posedge clk) begin
        if (rst) begin
            nonempty <= 1'b0;
            full <= 1'b0;
        end else begin
            if (!nonempty) begin
                if (push) begin
                    data0 <= in_data;
                    nonempty <= 1'b1;
                    full <= 1'b0;
                end
            end else if (!full) begin
                if (push && pop) begin
                    data0 <= in_data;
                    nonempty <= 1'b1;
                    full <= 1'b0;
                end else if (push) begin
                    data1 <= in_data;
                    nonempty <= 1'b1;
                    full <= 1'b1;
                end else if (pop) begin
                    nonempty <= 1'b0;
                    full <= 1'b0;
                end
            end else begin
                if (pop) begin
                    data0 <= data1;
                    nonempty <= 1'b1;
                    full <= 1'b0;
                end
            end
        end
    end
endmodule