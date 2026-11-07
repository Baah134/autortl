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
    reg valid;
    reg full;

    wire push;
    wire pop;

    assign in_ready = !full || out_ready;
    assign out_valid = valid;
    assign out_data = data0;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    always @(posedge clk) begin
        if (rst) begin
            valid <= 1'b0;
            full <= 1'b0;
        end else begin
            if (push && !pop)
                valid <= 1'b1;
            else if (!push && pop)
                valid <= full;

            if (push && !pop && valid)
                full <= 1'b1;
            else if (!push && pop)
                full <= 1'b0;

            if (pop && full)
                data0 <= data1;
            else if (push && !valid)
                data0 <= in_data;
            else if (push && pop && valid && !full)
                data0 <= in_data;

            if (push && valid && !full && !pop)
                data1 <= in_data;
            else if (push && pop && full)
                data1 <= in_data;
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