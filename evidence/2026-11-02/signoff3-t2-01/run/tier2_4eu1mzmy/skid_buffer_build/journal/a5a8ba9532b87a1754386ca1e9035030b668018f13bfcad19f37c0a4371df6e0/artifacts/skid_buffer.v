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

reg [7:0] data0;
reg [7:0] data1;
reg nonempty;
reg full;

wire push;
wire pop;

assign in_ready = !full || out_ready;
assign out_valid = nonempty;
assign out_data = data0;

assign push = in_valid && in_ready;
assign pop = out_valid && out_ready;

always @(posedge clk) begin
    if (rst) begin
        nonempty <= 1'b0;
        full <= 1'b0;
    end else begin
        case ({push, pop})
            2'b10: begin
                if (!nonempty) begin
                    data0 <= in_data;
                    nonempty <= 1'b1;
                    full <= 1'b0;
                end else begin
                    data1 <= in_data;
                    nonempty <= 1'b1;
                    full <= 1'b1;
                end
            end
            2'b01: begin
                if (full) begin
                    data0 <= data1;
                    nonempty <= 1'b1;
                    full <= 1'b0;
                end else begin
                    nonempty <= 1'b0;
                    full <= 1'b0;
                end
            end
            2'b11: begin
                if (full) begin
                    data0 <= data1;
                    data1 <= in_data;
                end else if (nonempty) begin
                    data0 <= in_data;
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