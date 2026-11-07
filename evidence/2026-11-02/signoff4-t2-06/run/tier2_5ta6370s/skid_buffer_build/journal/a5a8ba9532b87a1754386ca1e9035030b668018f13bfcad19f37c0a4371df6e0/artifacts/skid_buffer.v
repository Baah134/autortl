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

    reg [7:0] front_data;
    reg [7:0] back_data;
    reg front_valid;
    reg back_valid;

    wire push;
    wire pop;

    assign out_valid = front_valid;
    assign in_ready = !back_valid || out_ready;
    assign out_data = front_data;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            front_valid <= 1'b0;
            back_valid <= 1'b0;
        end else begin
            case ({push, pop})
                2'b10: begin
                    if (!front_valid) begin
                        front_data <= in_data;
                        front_valid <= 1'b1;
                    end else begin
                        back_data <= in_data;
                        back_valid <= 1'b1;
                    end
                end

                2'b01: begin
                    if (back_valid) begin
                        front_data <= back_data;
                        back_valid <= 1'b0;
                    end else begin
                        front_valid <= 1'b0;
                    end
                end

                2'b11: begin
                    if (back_valid) begin
                        front_data <= back_data;
                        back_data <= in_data;
                    end else begin
                        front_data <= in_data;
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