`timescale 1ns/1ps
// Winner-only check at board timing (DIV=868), written after finding that
// the harness's winner flattened away uart_tx_core: uart_tx_tb.v's DIV=3
// instance names uart_tx_core, so inside the harness it exercised the
// baseline child file, not the winner. This testbench instantiates only the
// top `uart_tx`, so it can only test the winner.
//
// It sends all 256 byte values in order, with random idle gaps, input noise
// while busy, and resets in the middle of frames, and checks tx and in_ready
// after every edge and between edges with the same cycle-exact reference as
// uart_tx_tb.v (uart_tx_ref_check, compiled from that file).
module verify_winner_tb;
    reg clk = 0;
    always #5 clk = ~clk;

    reg        rst = 1, valid = 0;
    reg  [7:0] data = 0;
    wire       ready, tx;
    uart_tx dut(.clk(clk), .rst(rst), .in_data(data), .in_valid(valid), .in_ready(ready), .tx(tx));
    uart_tx_ref_check #(.DIV(868)) ref_chk(.clk(clk), .rst(rst), .in_valid(valid), .in_data(data),
                                          .dut_ready(ready), .dut_tx(tx));

    integer seed = 7, next_byte = 0, cycle = 0, errors, gap = 0, accepted = 0;
    integer frames_before = 0, aborted_before = 0, in_flight = -1;
    reg [255:0] completed = 0;               // byte values whose frame finished

    initial begin
        repeat (3) @(negedge clk);
        rst = 0;
        while (next_byte < 256 && cycle < 3000000) begin
            @(negedge clk);
            cycle = cycle + 1;
            // Three resets land mid-frame; the aborted byte is sent again.
            rst = (cycle == 400123 || cycle == 1300457 || cycle == 2100789);
            if (ready && !rst) begin
                if (gap > 0) begin
                    gap = gap - 1; valid = 0; data = $random(seed);
                end else begin
                    valid = 1; data = next_byte;
                end
            end else begin
                valid = $random(seed) & 1;       // ignored while busy
                data  = $random(seed);
            end
            @(posedge clk); #2;
            if (ref_chk.frames > frames_before) begin          // the in-flight byte finished
                frames_before = ref_chk.frames;
                if (in_flight >= 0) completed[in_flight] = 1'b1;
                in_flight = -1;
            end
            if (ref_chk.aborted > aborted_before) begin        // a reset cut it off: send it again
                aborted_before = ref_chk.aborted;
                if (in_flight >= 0) next_byte = in_flight;
                in_flight = -1;
            end
            if (valid && !rst && ref_chk.busy && ref_chk.elapsed == 0) begin
                // Accepted at this edge: move on, and maybe idle for a while after it.
                in_flight = next_byte;
                next_byte = next_byte + 1;
                accepted = accepted + 1;
                gap = ($random(seed) & 3) == 0 ? ($random(seed) & 255) : 0;
            end
        end
        // Let the last frame finish.
        valid = 0;
        repeat (10 * 868 + 10) @(negedge clk);
        if (ref_chk.frames > frames_before && in_flight >= 0) completed[in_flight] = 1'b1;
        errors = ref_chk.errors;
        if (completed !== {256{1'b1}}) begin errors = errors + 1; $display("FAIL not every byte value completed a frame"); end
        if (ref_chk.aborted < 3)  begin errors = errors + 1; $display("FAIL coverage: %0d mid-frame resets < 3", ref_chk.aborted); end
        if (ref_chk.back_to_back < 100) begin errors = errors + 1; $display("FAIL coverage: back-to-back %0d < 100", ref_chk.back_to_back); end
        if (ref_chk.busy_noise < 100000) begin errors = errors + 1; $display("FAIL coverage: busy-time valid %0d", ref_chk.busy_noise); end
        $display("winner at DIV=868: %0d frames completed, %0d accepted, %0d back-to-back, %0d aborted by reset, %0d cycles",
                 ref_chk.frames, accepted, ref_chk.back_to_back, ref_chk.aborted, cycle);
        if (errors == 0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end
endmodule
