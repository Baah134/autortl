`timescale 1ns/1ps
// Independent integration testbench for the v2 transmitter (shortened stop
// bit), written from design_spec.json without seeing any generated RTL.
//
// It instantiates only the top `uart_tx`, the board configuration at
// DIV=868, so it grades exactly what goes on the board and does not pin any
// child module (a v1 lesson: a testbench that names a child pins it, see
// taxonomy stale_companion_masks_inlined_candidate). All 256 byte values
// are sent, with random idle gaps, back-to-back frames, input noise while
// busy and resets in the middle of frames. A cycle-exact reference checks
// tx and in_ready after every rising edge and between edges.
module uart_tx_tb;
    localparam DIV = 868;
    localparam STOP = DIV - DIV / 16;          // 814
    reg clk = 0;
    always #5 clk = ~clk;

    reg        rst = 1, valid = 0;
    reg  [7:0] data = 0;
    wire       ready, tx;
    uart_tx dut(.clk(clk), .rst(rst), .in_data(data), .in_valid(valid), .in_ready(ready), .tx(tx));

    // ---- cycle-exact reference ----
    reg        busy = 0, exp_tx = 1, exp_ready = 1, started = 0, just_finished = 0;
    reg  [9:0] frame = 10'h3ff;
    integer    elapsed = 0, errors = 0, frames = 0, back_to_back = 0, aborted = 0, busy_noise = 0;
    reg        accepted_now = 0;
    always @(posedge clk) begin
        started = 1; accepted_now = 0;
        if (rst) begin
            if (busy) aborted = aborted + 1;
            busy = 0; exp_tx = 1; exp_ready = 1; just_finished = 0;
        end else if (!busy) begin
            if (valid) begin
                if (just_finished) back_to_back = back_to_back + 1;
                frame = {1'b1, data, 1'b0};
                busy = 1; elapsed = 0; exp_tx = 1'b0; exp_ready = 0; accepted_now = 1;
            end
            just_finished = 0;
        end else begin
            if (valid) busy_noise = busy_noise + 1;
            elapsed = elapsed + 1;
            if (elapsed == 9 * DIV + STOP) begin
                busy = 0; exp_tx = 1; exp_ready = 1; frames = frames + 1; just_finished = 1;
            end else begin
                exp_tx = frame[elapsed / DIV];
            end
        end
        #1;
        if (tx !== exp_tx || ready !== exp_ready) begin
            errors = errors + 1;
            if (errors <= 10)
                $display("FAIL t=%0t: expected tx=%b in_ready=%b, got tx=%b in_ready=%b (elapsed %0d)",
                         $time, exp_tx, exp_ready, tx, ready, elapsed);
        end
    end
    always @(negedge clk) begin
        if (started && (tx !== exp_tx || ready !== exp_ready)) begin
            errors = errors + 1;
            if (errors <= 10) $display("FAIL t=%0t: output changed between edges", $time);
        end
    end

    // ---- stimulus: every byte value through a complete frame ----
    integer seed = 11, next_byte = 0, cycle = 0, gap = 0, in_flight = -1, frames_seen = 0, aborted_seen = 0;
    reg [255:0] completed = 0;
    initial begin
        repeat (3) @(negedge clk);
        rst = 0;
        while (next_byte < 256 && cycle < 3000000) begin
            @(negedge clk);
            cycle = cycle + 1;
            rst = (cycle == 300123 || cycle == 1200457 || cycle == 2000789);
            if (ready && !rst) begin
                if (gap > 0) begin gap = gap - 1; valid = 0; data = $random(seed); end
                else begin valid = 1; data = next_byte; end
            end else begin
                valid = $random(seed) & 1;
                data  = $random(seed);
            end
            @(posedge clk); #2;
            if (frames > frames_seen) begin
                frames_seen = frames;
                if (in_flight >= 0) completed[in_flight] = 1'b1;
                in_flight = -1;
            end
            if (aborted > aborted_seen) begin
                aborted_seen = aborted;
                if (in_flight >= 0) next_byte = in_flight;
                in_flight = -1;
            end
            if (accepted_now) begin
                in_flight = next_byte;
                next_byte = next_byte + 1;
                gap = ($random(seed) & 3) == 0 ? ($random(seed) & 255) : 0;
            end
        end
        valid = 0;
        repeat (10 * DIV + 10) @(negedge clk);
        if (frames > frames_seen && in_flight >= 0) completed[in_flight] = 1'b1;
        if (completed !== {256{1'b1}}) begin errors = errors + 1; $display("FAIL not every byte value completed a frame"); end
        if (aborted < 3)        begin errors = errors + 1; $display("FAIL coverage: %0d mid-frame resets < 3", aborted); end
        if (back_to_back < 100) begin errors = errors + 1; $display("FAIL coverage: back-to-back %0d < 100", back_to_back); end
        if (busy_noise < 100000) begin errors = errors + 1; $display("FAIL coverage: busy-time valid %0d", busy_noise); end
        $display("v2 at DIV=868, STOP=%0d: %0d frames, %0d back-to-back, %0d aborted by reset, %0d cycles",
                 STOP, frames, back_to_back, aborted, cycle);
        if (errors == 0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end

    initial begin
        #(10 * 3200000);
        $display("TEST FAILED: watchdog");
        $finish;
    end
endmodule
