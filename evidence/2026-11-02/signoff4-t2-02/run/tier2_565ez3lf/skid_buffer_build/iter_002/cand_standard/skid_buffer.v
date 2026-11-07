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

    reg [7:0] head;
    reg [7:0] tail;
    reg head_valid;
    reg tail_valid;

    wire push;
    wire pop;

    assign in_ready = !tail_valid || out_ready;
    assign out_valid = head_valid;
    assign out_data = head;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            head_valid <= 1'b0;
            tail_valid <= 1'b0;
        end else begin
            case ({push, pop})
                2'b10: begin
                    if (head_valid) begin
                        tail <= in_data;
                        tail_valid <= 1'b1;
                    end else begin
                        head <= in_data;
                        head_valid <= 1'b1;
                    end
                end
                2'b01: begin
                    if (tail_valid) begin
                        head <= tail;
                        tail_valid <= 1'b0;
                    end else begin
                        head_valid <= 1'b0;
                    end
                end
                2'b11: begin
                    if (tail_valid) begin
                        head <= tail;
                        tail <= in_data;
                    end else begin
                        head <= in_data;
                    end
                end
                default: begin
                end
            endcase
        end
    end

endmodule

`timescale 1ns/1ps
// @latency 1
// Inherited minimum accepted-transfer age from transparent typed child wiring; not measured timing.
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