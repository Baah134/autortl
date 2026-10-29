`timescale 1ns/1ps
// Independent integration testbench for the harness-built UART transmitter,
// written from design_spec.json without seeing any generated RTL.
//
// Two copies run side by side from one clock: the top `uart_tx` at its
// default DIV=868 (the exact board timing, 115200 baud from 100 MHz), and
// `uart_tx_core` at DIV=3 so thousands of random frames finish quickly and
// the DIV parameter is shown to work, not only its default. A cycle-exact
// reference (uart_tx_ref_check) predicts tx and in_ready after every rising
// edge from the same inputs; any difference is an error. Coverage gates fail
// the test if it never saw back-to-back frames, mid-frame resets, input
// noise while busy, or every data bit at both levels.
module uart_tx_tb;
    reg clk = 0;
    always #5 clk = ~clk;

    // DIV=868 instance: the shipped top level.
    reg        rst_a = 1, valid_a = 0;
    reg  [7:0] data_a = 0;
    wire       ready_a, tx_a;
    uart_tx dut_a(.clk(clk), .rst(rst_a), .in_data(data_a), .in_valid(valid_a),
                  .in_ready(ready_a), .tx(tx_a));
    uart_tx_ref_check #(.DIV(868)) ref_a(.clk(clk), .rst(rst_a), .in_valid(valid_a), .in_data(data_a),
                                        .dut_ready(ready_a), .dut_tx(tx_a));

    // DIV=3 instance: the core with an overridden parameter.
    reg        rst_b = 1, valid_b = 0;
    reg  [7:0] data_b = 0;
    wire       ready_b, tx_b;
    uart_tx_core #(.DIV(3)) dut_b(.clk(clk), .rst(rst_b), .in_data(data_b), .in_valid(valid_b),
                                  .in_ready(ready_b), .tx(tx_b));
    uart_tx_ref_check #(.DIV(3)) ref_b(.clk(clk), .rst(rst_b), .in_valid(valid_b), .in_data(data_b),
                                      .dut_ready(ready_b), .dut_tx(tx_b));

    integer cycle, seed, errors;
    localparam CYCLES = 80000;

    // Stimulus changes at the falling edge, away from the sampling edge.
    initial begin
        seed = 20261029;
        for (cycle = 0; cycle < CYCLES; cycle = cycle + 1) begin
            @(negedge clk);
            // DIV=3: random traffic, random bytes, noise while busy, rare resets.
            rst_b   = (cycle < 3) || ($random(seed) % 997 == 0);
            valid_b = ($random(seed) % 4) != 0;
            data_b  = $random(seed);
            // DIV=868: an initial reset, back-to-back bytes with valid held
            // high, a gap, a reset in the middle of a frame, and data noise.
            rst_a   = (cycle < 3) || (cycle == 40000);
            valid_a = (cycle >= 10 && cycle < 35000) || (cycle >= 36000 && cycle < 60000) ||
                      (cycle >= 67000 && cycle < 67010);   // a short pulse while idle

            if (!ready_a || cycle % 5 == 0) data_a = $random(seed);   // ignored while busy
            if (cycle == 10) data_a = 8'h55;
        end
        errors = ref_a.errors + ref_b.errors;
        if (ref_a.frames < 8)          begin errors = errors + 1; $display("FAIL coverage: DIV=868 frames %0d < 8", ref_a.frames); end
        if (ref_a.back_to_back < 3)    begin errors = errors + 1; $display("FAIL coverage: DIV=868 back-to-back %0d < 3", ref_a.back_to_back); end
        if (ref_a.aborted < 1)         begin errors = errors + 1; $display("FAIL coverage: DIV=868 never reset mid-frame"); end
        if (ref_b.frames < 1500)       begin errors = errors + 1; $display("FAIL coverage: DIV=3 frames %0d < 1500", ref_b.frames); end
        if (ref_b.back_to_back < 500)  begin errors = errors + 1; $display("FAIL coverage: DIV=3 back-to-back %0d < 500", ref_b.back_to_back); end
        if (ref_b.aborted < 10)        begin errors = errors + 1; $display("FAIL coverage: DIV=3 mid-frame resets %0d < 10", ref_b.aborted); end
        if (ref_b.busy_noise < 1000)   begin errors = errors + 1; $display("FAIL coverage: DIV=3 busy-time valid %0d < 1000", ref_b.busy_noise); end
        if (ref_b.bit_levels != 16'hffff) begin errors = errors + 1; $display("FAIL coverage: DIV=3 data bit levels %h", ref_b.bit_levels); end
        $display("frames: DIV=868 %0d (back-to-back %0d, aborted %0d); DIV=3 %0d (back-to-back %0d, aborted %0d)",
                 ref_a.frames, ref_a.back_to_back, ref_a.aborted, ref_b.frames, ref_b.back_to_back, ref_b.aborted);
        if (errors == 0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end

    initial begin
        #(10 * (CYCLES + 1000));
        $display("TEST FAILED: watchdog");
        $finish;
    end
endmodule

// Cycle-exact reference for the spec: after accept edge k, bit i of
// {stop, data[7:0], start} is on tx after edge k+i*DIV; idle (tx=1,
// in_ready=1) again after edge k+10*DIV. Checks both outputs one time unit
// after every rising edge, and just before it to catch combinational outputs.
module uart_tx_ref_check #(parameter DIV = 868) (
    input wire clk, input wire rst, input wire in_valid, input wire [7:0] in_data,
    input wire dut_ready, input wire dut_tx
);
    reg        busy = 0, exp_tx = 1, exp_ready = 1;
    reg  [9:0] frame = 10'h3ff;
    integer    elapsed = 0;
    integer    errors = 0, frames = 0, back_to_back = 0, aborted = 0, busy_noise = 0;
    integer    i;
    reg        just_finished = 0;            // the previous edge ended a frame
    reg        started = 0;                  // a rising edge has happened
    reg [15:0] bit_levels = 0;               // bit 2*i+level seen for data bit i

    always @(posedge clk) begin
        started = 1;
        if (rst) begin
            if (busy) aborted = aborted + 1;
            busy = 0; exp_tx = 1; exp_ready = 1; just_finished = 0;
        end else if (!busy) begin
            if (in_valid) begin
                // Accepted at the first edge after the previous frame ended.
                if (just_finished) back_to_back = back_to_back + 1;
                frame = {1'b1, in_data, 1'b0};
                for (i = 0; i < 8; i = i + 1) bit_levels[2 * i + in_data[i]] = 1'b1;
                busy = 1; elapsed = 0; exp_tx = 1'b0; exp_ready = 0;
            end
            just_finished = 0;
        end else begin
            if (in_valid) busy_noise = busy_noise + 1;
            elapsed = elapsed + 1;
            if (elapsed == 10 * DIV) begin
                busy = 0; exp_tx = 1; exp_ready = 1; frames = frames + 1; just_finished = 1;
            end else begin
                exp_tx = frame[elapsed / DIV];
            end
        end
        #1;
        if (dut_tx !== exp_tx || dut_ready !== exp_ready) begin
            errors = errors + 1;
            if (errors <= 10)
                $display("FAIL DIV=%0d t=%0t: expected tx=%b in_ready=%b, got tx=%b in_ready=%b (elapsed %0d)",
                         DIV, $time, exp_tx, exp_ready, dut_tx, dut_ready, elapsed);
        end
    end

    // Outputs are registered: they must not move between rising edges.
    always @(negedge clk) begin
        if (started && (dut_tx !== exp_tx || dut_ready !== exp_ready)) begin
            errors = errors + 1;
            if (errors <= 10)
                $display("FAIL DIV=%0d t=%0t: output changed between edges (tx=%b in_ready=%b)",
                         DIV, $time, dut_tx, dut_ready);
        end
    end
endmodule
