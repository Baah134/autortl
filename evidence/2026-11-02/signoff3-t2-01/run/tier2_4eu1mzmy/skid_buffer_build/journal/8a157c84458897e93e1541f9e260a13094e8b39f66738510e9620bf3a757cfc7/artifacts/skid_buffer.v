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
reg [1:0] occupancy;
reg out_valid_reg;

wire push;
wire pop;

assign in_ready = (occupancy < 2) || out_ready;
assign out_valid = out_valid_reg;
assign out_data = data0;

assign push = in_valid && in_ready;
assign pop = out_valid && out_ready;

always @(posedge clk) begin
    if (rst) begin
        occupancy <= 2'd0;
        out_valid_reg <= 1'b0;
    end else begin
        case ({push, pop})
            2'b10: begin
                if (occupancy == 0)
                    data0 <= in_data;
                else if (occupancy == 1)
                    data1 <= in_data;
                occupancy <= occupancy + 1'b1;
                out_valid_reg <= 1'b1;
            end
            2'b01: begin
                if (occupancy == 2) begin
                    data0 <= data1;
                    out_valid_reg <= 1'b1;
                end else begin
                    out_valid_reg <= 1'b0;
                end
                occupancy <= occupancy - 1'b1;
            end
            2'b11: begin
                if (occupancy == 1)
                    data0 <= in_data;
                else if (occupancy == 2) begin
                    data0 <= data1;
                    data1 <= in_data;
                end
                occupancy <= occupancy;
                out_valid_reg <= (occupancy != 0);
            end
            default: begin
                occupancy <= occupancy;
                out_valid_reg <= (occupancy != 0);
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