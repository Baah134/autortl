`timescale 1ns/1ps
// End-to-end check of basys3_harness_echo before it touches the board.
// A PC model sends a back-to-back stream at 115,200 baud (868.06 clocks per
// bit, the real PC rate) and an independent receiver samples RsTx at bit
// centres (864 clocks per bit, the board's rate). Every echoed byte must
// match, in order, with no framing or overflow count.
module tb_board;
    reg clk = 0;
    always #5 clk = ~clk;

    reg  btnC = 0;
    reg  RsRx = 1;
    wire RsTx;
    wire [7:0] led;

    basys3_harness_echo dut (.clk(clk), .btnC(btnC), .RsRx(RsRx), .RsTx(RsTx), .led(led));

    localparam integer N = 96;
    localparam real PC_BIT_NS = 1.0e9 / 115200.0;   // 8680.6 ns
    localparam integer BOARD_BIT = 864;              // clocks

    reg [7:0] sent [0:N-1];
    integer i, b, errors = 0, received = 0;
    reg [31:0] seed = 32'h1234abcd;
    reg [7:0] byte_in;

    function [31:0] xorshift;
        input [31:0] x;
        reg [31:0] y;
        begin y = x ^ (x << 13); y = y ^ (y >> 17); xorshift = y ^ (y << 5); end
    endfunction

    task pc_send;
        input [7:0] value;
        integer k;
        begin
            RsRx = 0; #(PC_BIT_NS);
            for (k = 0; k < 8; k = k + 1) begin RsRx = value[k]; #(PC_BIT_NS); end
            RsRx = 1; #(PC_BIT_NS);
        end
    endtask

    initial begin
        for (i = 0; i < N; i = i + 1) begin
            if (i == 0) sent[i] = 8'h00;
            else if (i == 1) sent[i] = 8'hFF;
            else if (i == 2) sent[i] = 8'h55;
            else if (i == 3) sent[i] = 8'hAA;
            else begin seed = xorshift(seed); sent[i] = seed[7:0]; end
        end
        #(2000);
        for (i = 0; i < N; i = i + 1) pc_send(sent[i]);   // no gaps between frames
    end

    // Independent receiver on RsTx.
    initial begin : rx_model
        integer k;
        @(posedge clk);
        while (received < N) begin
            @(negedge RsTx);
            repeat (BOARD_BIT / 2) @(posedge clk);
            if (RsTx !== 1'b0) begin errors = errors + 1; $display("FAIL start bit not low"); end
            for (k = 0; k < 8; k = k + 1) begin
                repeat (BOARD_BIT) @(posedge clk);
                byte_in[k] = RsTx;
            end
            repeat (BOARD_BIT) @(posedge clk);
            if (RsTx !== 1'b1) begin errors = errors + 1; $display("FAIL stop bit not high at byte %0d", received); end
            if (byte_in !== sent[received]) begin
                errors = errors + 1;
                $display("FAIL byte %0d: got %02h expected %02h", received, byte_in, sent[received]);
            end
            received = received + 1;
        end
        if (led !== 8'h00) begin errors = errors + 1; $display("FAIL error counters %02h", led); end
        if (errors == 0) $display("TEST PASSED (%0d bytes echoed)", received);
        else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end

    initial begin
        #(200_000_000);
        $display("TEST FAILED: watchdog (%0d of %0d bytes)", received, N);
        $finish;
    end
endmodule
