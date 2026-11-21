`timescale 1ns/1ps
// @latency 1
module TopModule (
    input  wire       clk,
    input  wire       areset,
    input  wire       train_valid,
    input  wire       train_taken,
    output wire [1:0] state
);
    reg [1:0] counter;

    assign state = counter;

    always @(posedge clk or posedge areset) begin
        if (areset) begin
            counter <= 2'b01;
        end else if (train_valid) begin
            if (train_taken) begin
                if (counter != 2'b11)
                    counter <= counter + 2'd1;
            end else begin
                if (counter != 2'b00)
                    counter <= counter - 2'd1;
            end
        end
    end
endmodule