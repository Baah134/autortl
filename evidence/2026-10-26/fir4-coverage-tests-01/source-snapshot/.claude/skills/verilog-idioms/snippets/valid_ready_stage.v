// Valid/ready pipeline stage with correct backpressure (example; adapt only to a matching contract)
module vr_stage #(parameter W = 8) (
    input  wire         clk,
    input  wire         rst,
    input  wire         in_valid,
    output wire         in_ready,
    input  wire [W-1:0] in_data,
    output reg          out_valid,
    input  wire         out_ready,
    output reg  [W-1:0] out_data
);
    assign in_ready = !out_valid || out_ready;
    always @(posedge clk) begin
        if (rst) begin
            out_valid <= 1'b0;
        end else begin
            if (in_valid && in_ready) begin
                out_data  <= in_data;
                out_valid <= 1'b1;
            end else if (out_ready) begin
                out_valid <= 1'b0;
            end
        end
    end
endmodule
