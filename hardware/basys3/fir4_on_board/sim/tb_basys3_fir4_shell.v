`timescale 1ns / 1ps
// Self-checking testbench for the FIR4 shell. It drives the serial line the
// way scripts/fir_test.py does: a break, then chunks of samples, each
// followed by its two-byte replies. A behavioral model of
// y = 3x[n] - 5x[n-1] + 7x[n-2] - 2x[n-3], kept to 13 bits and
// sign-extended, checks every reply. A second break mid-stream must reset
// the filter history.
module tb_basys3_fir4_shell;
    parameter CPB   = 16;
    parameter N     = 256;
    parameter CHUNK = 16;

    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg  btnC = 1'b1;
    reg  rx   = 1'b1;
    wire tx;
    wire [7:0] led;
    wire led_break, led_overflow;

    basys3_fir4_shell #(.CLKS_PER_BIT(CPB)) dut (
        .clk(clk), .btnC(btnC), .RsRx(rx), .RsTx(tx), .led(led),
        .led_break(led_break), .led_overflow(led_overflow)
    );

    reg signed [7:0]  samples  [0:N-1];
    reg signed [15:0] expected [0:N-1];
    reg signed [7:0]  h1, h2, h3;
    integer errors = 0, checked = 0;
    integer i, base, k;

    function signed [15:0] model(input signed [7:0] x, input signed [7:0] a,
                                 input signed [7:0] b, input signed [7:0] c);
        reg signed [15:0] full;
        begin
            full  = 3 * x - 5 * a + 7 * b - 2 * c;
            model = {{3{full[12]}}, full[12:0]};
        end
    endfunction

    task send_byte(input [7:0] value);
        integer bit_i;
        begin
            rx = 1'b0;
            repeat (CPB) @(posedge clk);
            for (bit_i = 0; bit_i < 8; bit_i = bit_i + 1) begin
                rx = value[bit_i];
                repeat (CPB) @(posedge clk);
            end
            rx = 1'b1;
            repeat (CPB) @(posedge clk);
        end
    endtask

    task send_break;
        begin
            rx = 1'b0;
            repeat (12 * CPB) @(posedge clk);
            rx = 1'b1;
            repeat (12 * CPB) @(posedge clk);
            h1 = 0; h2 = 0; h3 = 0;
        end
    endtask

    task recv_byte(output [7:0] value);
        integer bit_i;
        begin
            @(negedge tx);
            repeat (CPB / 2) @(posedge clk);
            for (bit_i = 0; bit_i < 8; bit_i = bit_i + 1) begin
                repeat (CPB) @(posedge clk);
                value[bit_i] = tx;
            end
            repeat (CPB) @(posedge clk);
            if (tx !== 1'b1) begin
                $display("ERROR: bad stop bit from DUT at %0t", $time);
                errors = errors + 1;
            end
        end
    endtask

    task run_chunk(input integer first, input integer count);
        integer j;
        reg [7:0] lo, hi;
        begin
            for (j = first; j < first + count; j = j + 1) begin
                expected[j] = model(samples[j], h1, h2, h3);
                h3 = h2; h2 = h1; h1 = samples[j];
            end
            fork
                begin : sender
                    integer s;
                    for (s = first; s < first + count; s = s + 1) send_byte(samples[s]);
                end
                begin : receiver
                    integer r;
                    for (r = first; r < first + count; r = r + 1) begin
                        recv_byte(lo);
                        recv_byte(hi);
                        if ({hi, lo} !== expected[r]) begin
                            $display("ERROR: sample %0d x=%0d expected %0d got %0d",
                                     r, samples[r], expected[r], $signed({hi, lo}));
                            errors = errors + 1;
                        end
                        checked = checked + 1;
                    end
                end
            join
        end
    endtask

    initial begin
        samples[0] = 8'sd127;  samples[1] = -8'sd128; samples[2] = 8'sd127;
        samples[3] = -8'sd128; samples[4] = -8'sd1;   samples[5] = 8'sd0;
        for (i = 6; i < N; i = i + 1) samples[i] = $random;
        // Worst-case magnitudes: +127 on positive taps, -128 on negative taps.
        samples[N/2]     = -8'sd128; samples[N/2 + 1] = 8'sd127;
        samples[N/2 + 2] = -8'sd128; samples[N/2 + 3] = 8'sd127;

        repeat (10) @(posedge clk);
        btnC = 1'b0;
        repeat (10) @(posedge clk);

        send_break;
        for (base = 0; base < N; base = base + CHUNK) begin
            if (base == N / 2) send_break;
            run_chunk(base, (N - base < CHUNK) ? N - base : CHUNK);
        end

        if (led_overflow !== 1'b0) begin
            $display("ERROR: input overflow flag set");
            errors = errors + 1;
        end
        if (led_break !== 1'b1) begin
            $display("ERROR: break flag not set");
            errors = errors + 1;
        end
        if (errors == 0 && checked == N)
            $display("PASS: %0d filter outputs matched the model, including a mid-stream restart", checked);
        else
            $display("FAIL: %0d errors, %0d of %0d outputs checked", errors, checked, N);
        $finish;
    end

    initial begin
        #(N * 40 * CPB * 10 + 100000);
        $display("FAIL: timeout after %0d of %0d outputs", checked, N);
        $finish;
    end
endmodule
