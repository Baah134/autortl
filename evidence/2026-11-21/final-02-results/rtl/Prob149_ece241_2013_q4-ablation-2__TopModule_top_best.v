`timescale 1ns/1ps
// @latency 1
module TopModule_top (
    input wire clk,
    input wire reset,
    input wire [2:0] s,
    output wire fr2,
    output wire fr1,
    output wire fr0,
    output wire dfr
);
    reg [3:0] valve_state;
    reg sensor_valid;
    reg dfr_next;

    assign {fr2, fr1, fr0, dfr} = valve_state;

    // Ordered-level check for reset low. Columns are 000, 001, 011, 111.
    // Prior (level, dfr)     Next dfr
    //       (0, 1)           1 1 1 0
    //       (1, 0)           1 0 1 0
    //       (1, 1)           1 1 1 0
    //       (2, 0)           1 0 0 0
    //       (2, 1)           1 0 1 0
    //       (3, 0)           1 0 0 0
    // Each row holds for 010, 100, 101, and 110. Reset sets 1111
    // for every row and sensor code. The RTL matches all 96 cases.
    always @(*) begin
        sensor_valid = 1'b1;
        dfr_next = 1'b0;
        case (s)
            3'b000: dfr_next = 1'b1;
            3'b001: dfr_next = fr1 & dfr;
            3'b011: dfr_next = fr1 | dfr;
            3'b111: dfr_next = 1'b0;
            default: sensor_valid = 1'b0;
        endcase
    end

    always @(posedge clk) begin
        if (reset)
            valve_state <= 4'b1111;
        else if (sensor_valid)
            valve_state <= {~s[0], ~s[1], ~s[2], dfr_next};
    end
endmodule