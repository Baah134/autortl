`timescale 1ns / 1ps
// Self-checking testbench for the Basys 3 echo. MODE selects a scenario:
//   0  exact-rate stream of N bytes, then a start-bit glitch, a frame with
//      a low stop bit, a break followed by a good byte, and reset clearing
//      the sticky flags
//   1  sender SEND_CPB clocks per bit (slightly fast): every byte must
//      return in order and the overflow flag must stay clear
//   2  sender much faster than the echo: the overflow flag must latch
// Short bit periods keep the simulation fast.
module tb_basys3_uart_echo;
    parameter MODE      = 0;
    parameter CPB       = 16;
    parameter SEND_CPB  = CPB;
    parameter N         = 64;
    parameter FIFO_LOG2 = 4;

    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg  btnC = 1'b1;
    reg  rx   = 1'b1;
    wire tx;
    wire [7:0] led;
    wire overflow, frame_error;

    basys3_uart_echo #(.CLKS_PER_BIT(CPB), .FIFO_DEPTH_LOG2(FIFO_LOG2)) dut (
        .clk(clk), .btnC(btnC), .RsRx(rx), .RsTx(tx), .led(led),
        .led_frame_err(frame_error), .led_overflow(overflow)
    );

    reg [7:0] sent [0:N-1];
    integer errors   = 0;
    integer received = 0;
    integer tx_falls = 0;
    integer i, j, falls_before;
    reg [7:0] led_before;

    always @(negedge tx) tx_falls = tx_falls + 1;

    task send_frame(input [7:0] b, input stop_bit, input integer bit_clks);
        integer k;
        begin
            rx = 1'b0;
            repeat (bit_clks) @(posedge clk);
            for (k = 0; k < 8; k = k + 1) begin
                rx = b[k];
                repeat (bit_clks) @(posedge clk);
            end
            rx = stop_bit;
            repeat (bit_clks) @(posedge clk);
            rx = 1'b1;
        end
    endtask

    task recv_byte(output [7:0] b);
        integer k;
        begin
            @(negedge tx);
            repeat (CPB / 2) @(posedge clk);
            if (tx !== 1'b0) begin
                $display("ERROR: start bit not low at %0t", $time);
                errors = errors + 1;
            end
            for (k = 0; k < 8; k = k + 1) begin
                repeat (CPB) @(posedge clk);
                b[k] = tx;
            end
            repeat (CPB) @(posedge clk);
            if (tx !== 1'b1) begin
                $display("ERROR: stop bit not high at %0t", $time);
                errors = errors + 1;
            end
        end
    endtask

    task check(input cond, input [8*48-1:0] what);
        if (!cond) begin
            $display("ERROR: %0s at %0t", what, $time);
            errors = errors + 1;
        end
    endtask

    initial begin
        for (i = 0; i < N; i = i + 1) sent[i] = $random;
        sent[0] = 8'h00;
        sent[1] = 8'hFF;
        sent[2] = 8'h55;
        sent[3] = 8'hAA;

        repeat (10) @(posedge clk);
        btnC = 1'b0;
        repeat (10) @(posedge clk);

        if (MODE == 2) begin
            for (i = 0; i < N; i = i + 1) send_frame(sent[i], 1'b1, SEND_CPB);
            repeat (4 * CPB) @(posedge clk);
            check(overflow === 1'b1, "overflow flag did not latch");
        end else begin
            fork
                begin : sender
                    for (i = 0; i < N; i = i + 1) send_frame(sent[i], 1'b1, SEND_CPB);
                end
                begin : monitor
                    reg [7:0] got;
                    for (j = 0; j < N; j = j + 1) begin
                        recv_byte(got);
                        if (got !== sent[j]) begin
                            $display("ERROR: byte %0d expected %02h got %02h", j, sent[j], got);
                            errors = errors + 1;
                        end
                        received = received + 1;
                    end
                end
            join
            check(led[7:0] === sent[N-1], "led does not show last byte");
            check(overflow === 1'b0, "overflow flag set without overflow");
            check(frame_error === 1'b0, "frame error flag set on good frames");
        end

        if (MODE == 0) begin
            repeat (2 * CPB) @(posedge clk);
            falls_before = tx_falls;
            led_before   = led[7:0];

            // A low pulse shorter than half a bit is not a start bit.
            rx = 1'b0;
            repeat (CPB / 4) @(posedge clk);
            rx = 1'b1;
            repeat (12 * CPB) @(posedge clk);
            check(tx_falls == falls_before, "glitch produced an echo");
            check(led[7:0] === led_before, "glitch changed the received byte");
            check(frame_error === 1'b0, "glitch raised a frame error");

            // A frame with a low stop bit is rejected and flagged.
            send_frame(8'h3C, 1'b0, CPB);
            repeat (12 * CPB) @(posedge clk);
            check(tx_falls == falls_before, "bad frame was echoed");
            check(led[7:0] === led_before, "bad frame updated the received byte");
            check(frame_error === 1'b1, "frame error flag did not latch");

            // A break (line held low for 12 bit times) must not echo a phantom
            // byte, and the next good byte must still come back.
            rx = 1'b0;
            repeat (12 * CPB) @(posedge clk);
            rx = 1'b1;
            repeat (12 * CPB) @(posedge clk);
            check(tx_falls == falls_before, "break produced an echo");
            fork
                send_frame(8'hA5, 1'b1, CPB);
                begin : after_break
                    reg [7:0] got;
                    recv_byte(got);
                    check(got === 8'hA5, "byte after break not echoed correctly");
                end
            join
            check(led[7:0] === 8'hA5, "led does not show the byte after the break");

            btnC = 1'b1;
            repeat (10) @(posedge clk);
            btnC = 1'b0;
            repeat (10) @(posedge clk);
            check(frame_error === 1'b0 && overflow === 1'b0, "reset did not clear flags");
        end

        if (errors == 0 && MODE == 2)
            $display("PASS: mode 2, %0d bytes sent, overflow flag latched", N);
        else if (errors == 0)
            $display("PASS: mode %0d, %0d bytes sent, %0d echoed", MODE, N, received);
        else
            $display("FAIL: mode %0d, %0d errors, %0d of %0d bytes echoed", MODE, errors, received, N);
        $finish;
    end

    initial begin
        #((N + 20) * SEND_CPB * 10 * 10 * 2);
        $display("FAIL: timeout in mode %0d after %0d of %0d bytes", MODE, received, N);
        $finish;
    end
endmodule
