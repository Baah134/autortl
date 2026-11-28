`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input  wire clk,
    input  wire reset,
    input  wire in,
    output wire done
);
    localparam [3:0] IDLE     = 4'd0;
    localparam [3:0] STOP     = 4'd9;
    localparam [3:0] RECOVERY = 4'd10;

    (* fsm_encoding = "none" *) reg [3:0] state;
    reg done_reg;

    function [63:0] make_state_table;
        input integer low_bit;
        input integer high_bit;
        integer address;
        reg [3:0] current_state;
        reg [3:0] incremented_state;
        reg [3:0] next_value;
        reg serial_in;
        begin
            make_state_table = 64'b0;
            for (address = 0; address < 32; address = address + 1) begin
                current_state = address[3:0];
                serial_in = address[4];
                incremented_state = current_state + 4'd1;
                next_value = IDLE;

                if ((current_state > IDLE) && (current_state < STOP))
                    next_value = incremented_state;
                else if (!serial_in) begin
                    if ((current_state == IDLE) || (current_state == STOP))
                        next_value = incremented_state;
                    else if (current_state == RECOVERY)
                        next_value = RECOVERY;
                end

                make_state_table[address]      = next_value[low_bit];
                make_state_table[address + 32] = next_value[high_bit];
            end
        end
    endfunction

    // Each table describes two five-input functions for synthesis to pack.
    localparam [63:0] STATE_BITS_20 = make_state_table(0, 2);
    localparam [63:0] STATE_BITS_31 = make_state_table(1, 3);

    wire [4:0] table_address;
    wire [5:0] upper_address;
    wire [3:0] next_state;
    wire next_done;

    assign table_address = {in, state};
    assign upper_address = {1'b1, table_address};
    assign next_state[0] = STATE_BITS_20[table_address];
    assign next_state[2] = STATE_BITS_20[upper_address];
    assign next_state[1] = STATE_BITS_31[table_address];
    assign next_state[3] = STATE_BITS_31[upper_address];
    assign next_done = (state == STOP) && in;
    assign done = done_reg;

    always @(posedge clk) begin
        if (reset) begin
            state    <= IDLE;
            done_reg <= 1'b0;
        end else begin
            state    <= next_state;
            done_reg <= next_done;
        end
    end
endmodule