`timescale 1ns/1ps
// Independent cycle reference for the DEFAULT 32-bit counter contract.
// Flags reflect the count BEFORE this edge, even on load/disabled edges.
// Overflow holds while disabled; reset > load > enable. Reset is synchronous.
module counter_tb;
    reg clk, rst, enable, load;
    reg [31:0] load_val;
    wire [31:0] count;
    wire at_zero, below_low, below_mid, below_high, overflow;
    reg [31:0] reference_count;
    reg reference_zero, reference_low, reference_mid, reference_high;
    reg reference_overflow;
    reg [36:0] before_reset;
    reg [31:0] random_state, random_control;
    integer errors, checked_edges, i;

    counter dut (.clk(clk), .rst(rst), .enable(enable), .load(load),
                 .load_val(load_val), .count(count), .at_zero(at_zero),
                 .below_low(below_low), .below_mid(below_mid),
                 .below_high(below_high), .overflow(overflow));
    always #5 clk = ~clk;

    // This checker never reads DUT internals or uses DUT outputs as reference state.
    // Blocking reference updates intentionally calculate flags before next count.
    always @(posedge clk) begin
        if (rst) begin
            reference_count = 32'd0;
            reference_overflow = 1'b0;
            reference_zero = 1'b1;
            reference_low = 1'b1;
            reference_mid = 1'b1;
            reference_high = 1'b1;
        end else begin
            reference_zero = (reference_count == 32'd0);
            reference_low = (reference_count < 32'd100);
            reference_mid = (reference_count < 32'd500);
            reference_high = (reference_count < 32'd1000);
            if (load) begin
                reference_count = load_val;
                reference_overflow = 1'b0;
            end else if (enable) begin
                reference_overflow = (reference_count == 32'hffffffff);
                reference_count = reference_count + 32'd1;
            end
        end
        #1; // observe sequential nonblocking assignments after the active edge
        checked_edges = checked_edges + 1;
        if ({count, at_zero, below_low, below_mid, below_high, overflow} !==
            {reference_count, reference_zero, reference_low, reference_mid,
             reference_high, reference_overflow}) begin
            errors = errors + 1;
            $display("FAIL edge=%0d rst=%b enable=%b load=%b load_val=%h", checked_edges, rst, enable, load, load_val);
            $display(" expected count=%h zero/low/mid/high/overflow=%b%b%b%b%b", reference_count,
                     reference_zero, reference_low, reference_mid, reference_high, reference_overflow);
            $display(" actual   count=%h zero/low/mid/high/overflow=%b%b%b%b%b", count,
                     at_zero, below_low, below_mid, below_high, overflow);
        end
    end

    // All ordinary controls change on falling edges. Return after checker completes.
    task cycle;
        input next_rst, next_enable, next_load;
        input [31:0] next_value;
        begin
            @(negedge clk);
            rst = next_rst; enable = next_enable; load = next_load; load_val = next_value;
            @(posedge clk); #2;
        end
    endtask

    task load_and_cross;
        input [31:0] value;
        begin
            cycle(0, 1, 1, value); // load wins over simultaneous enable
            cycle(0, 0, 0, 32'h12345678); // disabled count; flags must still update
            cycle(0, 1, 0, 32'd0);
            cycle(0, 1, 0, 32'd0);
            cycle(0, 0, 0, 32'd0);
        end
    endtask

    function [31:0] next_random;
        input [31:0] state;
        reg [31:0] value;
        begin
            value = state ^ (state << 13);
            value = value ^ (value >> 17);
            next_random = value ^ (value << 5);
        end
    endfunction

    initial begin
        clk = 0; rst = 1; enable = 0; load = 0; load_val = 0;
        errors = 0; checked_edges = 0;
        reference_count = 0; reference_overflow = 0;
        reference_zero = 1; reference_low = 1; reference_mid = 1; reference_high = 1;
        random_state = 32'h6d2b79f5;

        cycle(1, 1, 1, 32'hffffffff); // reset priority over load and enable
        cycle(1, 0, 0, 0);
        cycle(0, 1, 0, 0); // zero flag must remain high while count becomes one
        cycle(0, 0, 0, 0); // zero flag must update even though count is held

        load_and_cross(32'd0);
        load_and_cross(32'd1);
        load_and_cross(32'd99);
        load_and_cross(32'd100);
        load_and_cross(32'd101);
        load_and_cross(32'd499);
        load_and_cross(32'd500);
        load_and_cross(32'd501);
        load_and_cross(32'd999);
        load_and_cross(32'd1000);
        load_and_cross(32'd1001);
        load_and_cross(32'd1024); // low ten bits zero must not imply below thresholds
        load_and_cross(32'd65536);
        load_and_cross(32'h80000000);
        load_and_cross(32'hffffffff);

        // Wrap, then disabled overflow hold, then enabled clear.
        cycle(0, 0, 1, 32'hfffffffe);
        cycle(0, 1, 0, 0);
        cycle(0, 1, 0, 0);
        repeat (4) cycle(0, 0, 0, 32'hffffffff);
        cycle(0, 1, 0, 0);
        // A load clears asserted overflow even with enable high.
        cycle(0, 1, 1, 32'hffffffff);
        cycle(0, 1, 0, 0);
        cycle(0, 1, 1, 32'd500);

        // Assert synchronous reset BETWEEN edges; every output must remain unchanged.
        cycle(0, 0, 1, 32'hdeadbeef);
        cycle(0, 0, 0, 0);
        @(negedge clk);
        enable = 1; load = 1; load_val = 32'hffffffff;
        before_reset = {count, at_zero, below_low, below_mid, below_high, overflow};
        #1; rst = 1;
        #1;
        if ({count, at_zero, below_low, below_mid, below_high, overflow} !== before_reset) begin
            errors = errors + 1;
            $display("FAIL synchronous reset changed outputs away from rising edge");
        end
        @(posedge clk); #2;
        cycle(0, 0, 0, 0);

        // 800 reproducible random control/load cycles; no simulator-global RNG.
        for (i = 0; i < 800; i = i + 1) begin
            random_state = next_random(random_state);
            random_control = random_state;
            random_state = next_random(random_state);
            cycle(random_control[7:3] == 5'b00000,
                  random_control[0], random_control[1], random_state);
        end
        // Finish in a defined disabled state and check all flags still settle.
        cycle(0, 0, 1, 32'd1000);
        cycle(0, 0, 0, 0);
        cycle(0, 0, 0, 0);
        if (checked_edges < 880) begin
            errors = errors + 1;
            $display("FAIL insufficient checked cycles: %0d", checked_edges);
        end
        if (errors == 0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors across %0d edges", errors, checked_edges);
        $finish;
    end

    initial begin
        #20000;
        $display("TEST FAILED: counter watchdog expired");
        $finish;
    end
endmodule
