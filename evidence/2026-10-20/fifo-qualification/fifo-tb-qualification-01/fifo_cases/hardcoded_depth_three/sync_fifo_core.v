`timescale 1ns/1ps
// @latency 1
// Qualification only. Never configured as a generator seed.
module sync_fifo_core #(parameter WIDTH=8, parameter DEPTH=3)(
    input clk, input rst, input [WIDTH-1:0] in_data,
    input in_valid, output in_ready, output [WIDTH-1:0] out_data,
    output out_valid, input out_ready);
    // clog2(DEPTH+1) remains positive for DEPTH=1; explicit wrap handles all depths.
    reg [$clog2(DEPTH+1)-1:0] read_pointer, write_pointer;
    reg [$clog2(DEPTH+1)-1:0] used;
    reg [WIDTH-1:0] memory [0:DEPTH-1];
    wire push = in_valid && in_ready;
    wire pop = out_valid && out_ready;
    assign in_ready = (used < 3) || out_ready;
    assign out_valid = (used != 0);
    assign out_data = memory[read_pointer];
    always @(posedge clk) begin
        if(rst) begin
            read_pointer <= 0;
            write_pointer <= 0;
            used <= 0;
        end else begin
            if(push) begin
                memory[write_pointer] <= in_data;
                if(write_pointer == DEPTH-1) write_pointer <= 0;
                else write_pointer <= write_pointer + 1'b1;
            end
            if(pop) begin
                if(read_pointer == DEPTH-1) read_pointer <= 0;
                else read_pointer <= read_pointer + 1'b1;
            end
            case({push,pop})
                2'b10: used <= used + 1'b1;
                2'b01: used <= used - 1'b1;
                2'b11: used <= used;
                default: used <= used;
            endcase
        end
    end
endmodule
