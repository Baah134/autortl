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

    function integer clog2;
        input integer value;
        integer temp;
        begin
            temp = value - 1;
            clog2 = 0;
            while (temp > 0) begin
                clog2 = clog2 + 1;
                temp = temp >> 1;
            end
        end
    endfunction

    localparam PTR_WIDTH = (DEPTH <= 1) ? 1 : clog2(DEPTH);

    reg [WIDTH-1:0] data_mem [0:DEPTH-1];
    reg last_mem [0:DEPTH-1];

    reg [PTR_WIDTH-1:0] read_ptr;
    reg [PTR_WIDTH-1:0] write_ptr;
    reg [DEPTH:0] occupancy_state;

    reg [WIDTH-1:0] head_data;
    reg head_last;

    wire full_state;
    wire push;
    wire pop;
    wire more_than_one;
    wire [PTR_WIDTH-1:0] next_read_ptr;

    assign full_state = occupancy_state[DEPTH];
    assign out_valid = !occupancy_state[0];
    assign in_ready = !full_state || out_ready;
    assign out_data = head_data;
    assign out_last = head_last;

    assign push = in_valid && in_ready;
    assign pop = out_valid && out_ready;

    assign next_read_ptr = (read_ptr == DEPTH - 1) ? {PTR_WIDTH{1'b0}} :
                           read_ptr + 1'b1;

    generate
        if (DEPTH > 1) begin: gen_multiple_entries
            assign more_than_one = |occupancy_state[DEPTH:2];

            always @(posedge clk) begin
                if (rst) begin
                    head_data <= {WIDTH{1'b0}};
                    head_last <= 1'b0;
                end else if (push && occupancy_state[0]) begin
                    head_data <= in_data;
                    head_last <= in_last;
                end else if (pop) begin
                    if (more_than_one) begin
                        head_data <= data_mem[next_read_ptr];
                        head_last <= last_mem[next_read_ptr];
                    end else if (push) begin
                        head_data <= in_data;
                        head_last <= in_last;
                    end
                end
            end
        end else begin: gen_single_entry
            assign more_than_one = 1'b0;

            always @(posedge clk) begin
                if (rst) begin
                    head_data <= {WIDTH{1'b0}};
                    head_last <= 1'b0;
                end else if (push && occupancy_state[0]) begin
                    head_data <= in_data;
                    head_last <= in_last;
                end else if (pop && push) begin
                    head_data <= in_data;
                    head_last <= in_last;
                end
            end
        end
    endgenerate

    always @(posedge clk) begin
        if (rst) begin
            read_ptr <= 0;
            write_ptr <= 0;
            occupancy_state <= {{DEPTH{1'b0}}, 1'b1};
        end else begin
            if (push) begin
                data_mem[write_ptr] <= in_data;
                last_mem[write_ptr] <= in_last;
                if (write_ptr == DEPTH - 1)
                    write_ptr <= 0;
                else
                    write_ptr <= write_ptr + 1'b1;
            end

            if (pop) begin
                if (read_ptr == DEPTH - 1)
                    read_ptr <= 0;
                else
                    read_ptr <= read_ptr + 1'b1;
            end

            case ({push, pop})
                2'b10: occupancy_state <= occupancy_state << 1;
                2'b01: occupancy_state <= occupancy_state >> 1;
                default: occupancy_state <= occupancy_state;
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