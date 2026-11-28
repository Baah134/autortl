`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output wire done
);

    localparam [3:0] IDLE = 4'd0;
    localparam [3:0] STOP = 4'd9;

    (* fsm_encoding = "none" *) reg [3:0] progress;
    reg done_reg;

    wire [4:0] table_index;
    wire [3:0] progress_next;
    wire stop_success;

    // Each pair shares the same five inputs. Within each 32-bit table,
    // bits 15:0 cover in=0 and bits 31:16 cover in=1.
    localparam [31:0] NEXT_BIT_0 = 32'h0154_0155;
    localparam [31:0] NEXT_BIT_1 = 32'h0066_0666;
    localparam [31:0] NEXT_BIT_2 = 32'h0078_0078;
    localparam [31:0] NEXT_BIT_3 = 32'h0180_0780;

    assign table_index = {in, progress};
    assign progress_next[0] = NEXT_BIT_0[table_index];
    assign progress_next[1] = NEXT_BIT_1[table_index];
    assign progress_next[2] = NEXT_BIT_2[table_index];
    assign progress_next[3] = NEXT_BIT_3[table_index];

    assign stop_success = in & (progress == STOP);
    assign done = done_reg;

    // For in=0 and in=1 respectively, idle goes to (1, 0),
    // each data phase 1 through 8 advances by one, stop goes to
    // (10, 0), and recovery goes to (10, 0). Reset overrides both
    // input values in every phase.
    // Stop success pulses done on edge ten and permits a start on
    // edge eleven. A recovery high permits a start on the next edge.
    always @(posedge clk) begin
        if (reset) begin
            progress <= IDLE;
            done_reg <= 1'b0;
        end else begin
            progress <= progress_next;
            done_reg <= stop_success;
        end
    end

endmodule