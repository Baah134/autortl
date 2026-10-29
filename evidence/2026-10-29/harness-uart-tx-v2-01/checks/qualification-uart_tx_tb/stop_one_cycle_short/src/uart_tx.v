`timescale 1ns/1ps
// Hand-written v2 reference used only to qualify uart_tx_tb.v: the testbench
// must pass this and fail every mutant in mutants.json. It is not the design
// that goes to the board; the harness generates that from design_spec.json.
module uart_tx_core #(parameter DIV = 868) (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] in_data,
    input  wire       in_valid,
    output reg        in_ready,
    output reg        tx
);
    localparam STOP = DIV - DIV / 16;
    localparam CW = $clog2(DIV);
    reg [CW-1:0] tick;        // cycles elapsed within the current bit
    reg [3:0]    bitn;        // 0 = start, 1..8 = data, 9 = stop
    reg [9:0]    frame;       // {stop, data, start}, shifted out LSB first
    wire [CW-1:0] last = (bitn == 4'd9) ? STOP - 2 : DIV - 1;

    always @(posedge clk) begin
        if (rst) begin
            in_ready <= 1'b1;
            tx       <= 1'b1;
            tick     <= 0;
            bitn     <= 0;
        end else if (in_ready) begin
            if (in_valid) begin
                frame    <= {1'b1, in_data, 1'b0};
                tx       <= 1'b0;
                in_ready <= 1'b0;
                tick     <= 0;
                bitn     <= 0;
            end
        end else if (tick == last) begin
            tick <= 0;
            if (bitn == 4'd9) begin
                in_ready <= 1'b1;
                tx       <= 1'b1;
            end else begin
                bitn <= bitn + 4'd1;
                tx   <= frame[bitn + 4'd1];
            end
        end else begin
            tick <= tick + 1'b1;
        end
    end
endmodule

module uart_tx (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] in_data,
    input  wire       in_valid,
    output wire       in_ready,
    output wire       tx
);
    uart_tx_core u_core(.clk(clk), .rst(rst), .in_data(in_data), .in_valid(in_valid),
                        .in_ready(in_ready), .tx(tx));
endmodule
