`timescale 1ns/1ps
// @latency 1
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

    reg [7:0] head_data;
    reg [7:0] tail_data;
    reg empty;
    reg full;

    wire push;
    wire pop;

    assign in_ready = ~full || out_ready;
    assign out_valid = ~empty;
    assign out_data = head_data;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            empty <= 1'b1;
            full <= 1'b0;
        end else begin
            case ({push, pop})
                2'b10: begin
                    empty <= 1'b0;
                    full <= ~empty;
                end
                2'b01: begin
                    empty <= ~full;
                    full <= 1'b0;
                end
                default: begin
                    empty <= empty;
                    full <= full;
                end
            endcase

            if (empty) begin
                if (push)
                    head_data <= in_data;
            end else if (full) begin
                if (pop) begin
                    head_data <= tail_data;
                    if (push)
                        tail_data <= in_data;
                end
            end else begin
                if (push && pop)
                    head_data <= in_data;
                else if (push)
                    tail_data <= in_data;
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