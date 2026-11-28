`timescale 1ns/1ps
// @latency 0
module debouncer_top (
    input wire clk,
    input wire rst,
    input wire noisy,
    output wire clean
);
    reg [2:0] run_state;
    reg clean_reg;

    assign clean = clean_reg;

    always @(posedge clk) begin
        if (rst) begin
            run_state <= 3'b000;
            clean_reg <= 1'b0;
        end else if (noisy == clean_reg) begin
            run_state <= 3'b000;
        end else if (run_state == 3'b100) begin
            clean_reg <= noisy;
            run_state <= 3'b000;
        end else if (run_state == 3'b000) begin
            run_state <= 3'b001;
        end else begin
            run_state <= {run_state[1:0], run_state[2] ^ run_state[0]};
        end
    end
endmodule