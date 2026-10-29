`timescale 1ns / 1ps
// Generic self-checking testbench for stream_shell + one harness winner.
// stim.hex / expect.hex (one byte per line, written by `python -m hwsuite
// sim` from the independent reference model) hold N transactions and their
// results. The bench drives the serial line like the PC does: a break, then
// chunks of transactions, each followed by its results; a second break at
// RESTART_AT restarts the design, and the model restarts there too.
module tb_stream_shell;
    parameter IN_BYTES   = 1;
    parameter OUT_BYTES  = 1;
    parameter N          = 400;
    parameter RESTART_AT = 200;
    parameter CHUNK      = 16;
    parameter CPB        = 16;
    parameter STALL_LOG2 = 12;            // up to 4096 cycles: longer than a chunk of traffic
    // Coverage the run must reach, or it fails: cycles with a result held
    // under backpressure, and (when the design's contract allows it) cycles
    // with an input accepted while a result retires.
    parameter MIN_STALLED = 200;
    parameter REQUIRE_OVERLAP = 1;
    parameter MIN_OVERLAP = 20;
    localparam MAX_BYTES = 8 * 4096;

    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg  btnC = 1'b1;
    reg  rx   = 1'b1;
    wire tx;
    wire [7:0] led;
    wire led_break, led_overflow;

    stream_shell #(.IN_BYTES(IN_BYTES), .OUT_BYTES(OUT_BYTES), .CLKS_PER_BIT(CPB),
                   .STALL_LOG2(STALL_LOG2)) dut (
        .clk(clk), .btnC(btnC), .RsRx(rx), .RsTx(tx), .led(led),
        .led_break(led_break), .led_overflow(led_overflow)
    );

    integer stalled_cycles = 0, overlap_cycles = 0;
    always @(posedge clk) begin
        if (dut.dut_out_valid && !dut.dut_out_ready) stalled_cycles = stalled_cycles + 1;
        if (dut.dut_in_valid && dut.dut_in_ready && dut.dut_out_valid && dut.dut_out_ready)
            overlap_cycles = overlap_cycles + 1;
    end

    reg [7:0] stim [0:MAX_BYTES-1];
    reg [7:0] expected [0:MAX_BYTES-1];
    integer errors = 0, checked = 0, base, count;

    task send_byte(input [7:0] value);
        integer b;
        begin
            rx = 1'b0;
            repeat (CPB) @(posedge clk);
            for (b = 0; b < 8; b = b + 1) begin
                rx = value[b];
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
        end
    endtask

    task recv_byte(output [7:0] value);
        integer b;
        begin
            @(negedge tx);
            repeat (CPB / 2) @(posedge clk);
            for (b = 0; b < 8; b = b + 1) begin
                repeat (CPB) @(posedge clk);
                value[b] = tx;
            end
            repeat (CPB) @(posedge clk);
            if (tx !== 1'b1) begin
                $display("ERROR: bad stop bit from the shell at %0t", $time);
                errors = errors + 1;
            end
        end
    endtask

    task run_chunk(input integer first, input integer n);
        begin
            fork
                begin : sender
                    integer s;
                    for (s = first * IN_BYTES; s < (first + n) * IN_BYTES; s = s + 1)
                        send_byte(stim[s]);
                end
                begin : receiver
                    integer t, k, bad;
                    reg [7:0] got;
                    for (t = first; t < first + n; t = t + 1) begin
                        bad = 0;
                        for (k = 0; k < OUT_BYTES; k = k + 1) begin
                            recv_byte(got);
                            if (got !== expected[t * OUT_BYTES + k]) bad = 1;
                        end
                        if (bad) begin
                            if (errors < 10) $display("ERROR: transaction %0d result differs from the model", t);
                            errors = errors + 1;
                        end
                        checked = checked + 1;
                    end
                end
            join
        end
    endtask

    initial begin
        if (N * IN_BYTES > MAX_BYTES || N * OUT_BYTES > MAX_BYTES) begin
            $display("FAIL: vectors exceed MAX_BYTES");
            $finish;
        end
        $readmemh("stim.hex", stim, 0, N * IN_BYTES - 1);
        $readmemh("expect.hex", expected, 0, N * OUT_BYTES - 1);

        repeat (10) @(posedge clk);
        btnC = 1'b0;
        repeat (10) @(posedge clk);

        send_break;
        base = 0;
        while (base < N) begin
            if (base == RESTART_AT) send_break;
            count = CHUNK;
            if (base < RESTART_AT && base + count > RESTART_AT) count = RESTART_AT - base;
            if (base + count > N) count = N - base;
            run_chunk(base, count);
            base = base + count;
        end

        if (led_overflow !== 1'b0) begin
            $display("ERROR: input overflow flag set");
            errors = errors + 1;
        end
        if (led_break !== 1'b1) begin
            $display("ERROR: break flag not set");
            errors = errors + 1;
        end
        $display("COVERAGE: %0d cycles with a result held under backpressure, %0d cycles accepting while retiring",
                 stalled_cycles, overlap_cycles);
        if (stalled_cycles < MIN_STALLED) begin
            $display("ERROR: backpressure coverage %0d below %0d", stalled_cycles, MIN_STALLED);
            errors = errors + 1;
        end
        if (REQUIRE_OVERLAP && overlap_cycles < MIN_OVERLAP) begin
            $display("ERROR: overlap coverage %0d below %0d", overlap_cycles, MIN_OVERLAP);
            errors = errors + 1;
        end
        if (errors == 0 && checked == N)
            $display("PASS: %0d results matched the model, with a restart at %0d (stalled %0d, overlap %0d)",
                     checked, RESTART_AT, stalled_cycles, overlap_cycles);
        else
            $display("FAIL: %0d errors, %0d of %0d results checked", errors, checked, N);
        $finish;
    end

    initial begin
        #(64'd1 * N * (IN_BYTES + OUT_BYTES + 8) * 10 * CPB * 10 * 4 + 64'd5000000);
        $display("FAIL: timeout after %0d of %0d results", checked, N);
        $finish;
    end
endmodule
