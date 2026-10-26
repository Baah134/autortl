`timescale 1ns/1ps
// @latency 1
// Qualification reference only: never an input/seed to model generation.
module skid_buffer_core(input clk,input rst,input [7:0] in_data,
    input in_valid,output in_ready,output [7:0] out_data,
    output out_valid,input out_ready);
    reg [7:0] storage [0:1];
    reg read_pointer, write_pointer;
    reg [1:0] used;
    wire push = in_valid && in_ready;
    wire pop = out_valid && out_ready;
    assign in_ready = (used != 2) || out_ready;
    assign out_valid = (used != 0);
    assign out_data = storage[read_pointer];
    always @(posedge clk) begin
        if (rst) begin
            read_pointer <= 0;
            write_pointer <= 0;
            used <= 0;
        end else begin
            if (push) begin
                storage[write_pointer] <= in_data;
                write_pointer <= !write_pointer;
            end
            if (pop) read_pointer <= !read_pointer;
            case ({push,pop})
                2'b10: used <= used + 1'b1;
                2'b01: used <= used - 1'b1;
                default: used <= used;
            endcase
        end
    end
endmodule
