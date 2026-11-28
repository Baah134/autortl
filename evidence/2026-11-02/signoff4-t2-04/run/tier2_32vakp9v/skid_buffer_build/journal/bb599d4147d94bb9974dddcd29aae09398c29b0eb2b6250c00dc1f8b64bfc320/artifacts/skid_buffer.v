`timescale 1ns/1ps

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

    reg [7:0] data0;
    reg [7:0] data1;
    reg head_valid;
    reg tail_valid;

    wire push;
    wire pop;

    assign in_ready = !tail_valid || out_ready;
    assign out_valid = head_valid;
    assign out_data = data0;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            head_valid <= 1'b0;
            tail_valid <= 1'b0;
        end else begin
            if (!head_valid) begin
                if (push) begin
                    data0 <= in_data;
                    head_valid <= 1'b1;
                end
            end else if (!tail_valid) begin
                if (push && pop) begin
                    data0 <= in_data;
                end else if (push) begin
                    data1 <= in_data;
                    tail_valid <= 1'b1;
                end else if (pop) begin
                    head_valid <= 1'b0;
                end
            end else if (pop) begin
                data0 <= data1;
                if (push) begin
                    data1 <= in_data;
                end else begin
                    tail_valid <= 1'b0;
                end
            end
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
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