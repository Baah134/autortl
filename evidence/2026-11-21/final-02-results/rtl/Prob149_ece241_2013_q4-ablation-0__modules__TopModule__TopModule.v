`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire       clk,
    input  wire       reset,
    input  wire [2:0] s,
    output wire       fr2,
    output wire       fr1,
    output wire       fr0,
    output wire       dfr
);

    reg [2:0] level;
    reg [2:0] previous_sample;
    reg direction;

    wire legal = (!s[2] || s[1]) && (!s[1] || s[0]);
    wire from_lower = s[1] ? !previous_sample[1] : !previous_sample[0];
    wire from_higher = s[1] ? previous_sample[2] : previous_sample[1];

    assign fr2 = !level[0];
    assign fr1 = !level[1];
    assign fr0 = !level[2];
    assign dfr = direction;

    always @(posedge clk) begin
        if (reset) begin
            level           <= 3'b000;
            previous_sample <= 3'b000;
            direction       <= 1'b1;
        end else begin
            previous_sample <= s;
            if (legal) begin
                level <= s;
                if (s == 3'b000)
                    direction <= 1'b1;
                else if (s == 3'b111)
                    direction <= 1'b0;
                else if (s > level)
                    direction <= 1'b1;
                else if (s < level)
                    direction <= 1'b0;
                else if (from_higher)
                    direction <= 1'b0;
                else if (from_lower)
                    direction <= 1'b1;
            end
        end
    end

endmodule