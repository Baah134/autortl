`timescale 1ns/1ps
// AutoRTL starter design: deliberately unoptimised counter.
// Known slack: dead prev_count register, registered threshold flags,
// full-width comparisons, redundant count_next.
module counter #(
    parameter WIDTH       = 32,
    parameter THRESH_LOW  = 100,
    parameter THRESH_MID  = 500,
    parameter THRESH_HIGH = 1000
)(
    input  wire             clk,
    input  wire             rst,
    input  wire             enable,
    input  wire             load,
    input  wire [WIDTH-1:0] load_val,
    output reg  [WIDTH-1:0] count,
    output reg              at_zero,
    output reg              below_low,
    output reg              below_mid,
    output reg              below_high,
    output reg              overflow
);
    reg [WIDTH-1:0] prev_count;      // dead register (never read)
    reg [WIDTH-1:0] count_next;

    always @(posedge clk) begin
        if (rst) begin
            count      <= {WIDTH{1'b0}};
            prev_count <= {WIDTH{1'b0}};
            overflow   <= 1'b0;
        end else begin
            prev_count <= count;
            if (load) begin
                count    <= load_val;
                overflow <= 1'b0;
            end else if (enable) begin
                count_next = count + 1'b1;
                if (count == {WIDTH{1'b1}}) begin
                    overflow <= 1'b1;
                    count    <= {WIDTH{1'b0}};
                end else begin
                    overflow <= 1'b0;
                    count    <= count_next;
                end
            end
        end
    end

    // registered threshold flags: one cycle late AND extra FFs
    always @(posedge clk) begin
        if (rst) begin
            at_zero    <= 1'b1;
            below_low  <= 1'b1;
            below_mid  <= 1'b1;
            below_high <= 1'b1;
        end else begin
            at_zero    <= (count == {WIDTH{1'b0}});
            below_low  <= (count[9:0] < THRESH_LOW);
            below_mid  <= (count[9:0] < THRESH_MID);
            below_high <= (count[9:0] < THRESH_HIGH);
        end
    end
endmodule
