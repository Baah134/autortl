`timescale 1ns / 1ps
// Board-level simulation: a PC model sends bytes into RsRx 0.2% fast (as
// the real PC does), an independent receiver decodes RsTx, and every byte
// must come back in order with no overflow or frame error.
// Prints TEST PASSED / TEST FAILED.
module tb_board;
    localparam N = 40;
    localparam real BIT_NS = 8680.0 / 1.002;     // PC 0.2% fast
    reg clk = 0;
    always #5 clk = ~clk;

    reg btnC = 1, rx = 1;
    wire tx;
    wire [7:0] led;
    wire led_frame_err, led_overflow;
    basys3_harness_uart_tx dut(.clk(clk), .btnC(btnC), .RsRx(rx), .RsTx(tx),
                               .led(led), .led_frame_err(led_frame_err), .led_overflow(led_overflow));

    reg [7:0] sent [0:N-1];
    reg [7:0] got  [0:N-1];
    integer n_got = 0, i, b, errors = 0;

    task send_byte(input [7:0] value);
        begin
            rx = 0; #(BIT_NS);
            for (b = 0; b < 8; b = b + 1) begin rx = value[b]; #(BIT_NS); end
            rx = 1; #(BIT_NS);
        end
    endtask

    // Independent decoder of RsTx at the nominal 8680 ns per bit, sampling mid-bit.
    reg [7:0] shift;
    integer k;
    initial begin
        forever begin
            @(negedge tx);
            #(8680 / 2);
            if (tx !== 1'b0) begin errors = errors + 1; $display("FAIL glitch start bit at %0t", $time); end
            for (k = 0; k < 8; k = k + 1) begin #(8680); shift[k] = tx; end
            #(8680);
            if (tx !== 1'b1) begin errors = errors + 1; $display("FAIL stop bit low at %0t", $time); end
            if (n_got < N) got[n_got] = shift;
            n_got = n_got + 1;
        end
    end

    initial begin
        for (i = 0; i < N; i = i + 1) sent[i] = (i * 37 + 11) ^ (i << 3);
        sent[0] = 8'h00; sent[1] = 8'hff; sent[2] = 8'h55; sent[3] = 8'haa;
        #200 btnC = 0;
        #2000;
        for (i = 0; i < N; i = i + 1) send_byte(sent[i]);
        #(8680 * 10 * 6);
        if (n_got != N) begin errors = errors + 1; $display("FAIL received %0d of %0d bytes", n_got, N); end
        for (i = 0; i < N && i < n_got; i = i + 1)
            if (got[i] !== sent[i]) begin
                errors = errors + 1;
                if (errors <= 8) $display("FAIL byte %0d: sent %h got %h", i, sent[i], got[i]);
            end
        if (led_overflow)  begin errors = errors + 1; $display("FAIL overflow latched"); end
        if (led_frame_err) begin errors = errors + 1; $display("FAIL frame error latched"); end
        $display("board sim: sent %0d, received %0d", N, n_got);
        if (errors == 0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end
endmodule
