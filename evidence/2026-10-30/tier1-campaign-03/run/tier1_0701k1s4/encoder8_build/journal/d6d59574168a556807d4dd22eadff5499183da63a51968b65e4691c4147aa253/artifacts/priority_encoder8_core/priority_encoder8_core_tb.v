`timescale 1ns/1ps
module priority_encoder8_core_tb;
    reg clk = 0;
    reg rst = 1;
    reg [7:0] request = 0;
    wire [2:0] index;
    wire valid;
    integer errors = 0;
    integer pattern;
    priority_encoder8_core dut(.clk(clk), .rst(rst), .request(request),
                          .index(index), .valid(valid));
    always #5 clk = ~clk;

    task check_cycle;
        input reset_value;
        input [7:0] request_value;
        reg [2:0] old_index;
        reg old_valid;
        reg [2:0] expected_index;
        reg expected_valid;
        integer bit_number;
        begin
            @(negedge clk);
            old_index = index;
            old_valid = valid;
            rst = reset_value;
            request = request_value;
            expected_index = 0;
            expected_valid = 0;
            if (!reset_value) begin
                expected_valid = (request_value != 0);
                for (bit_number = 0; bit_number < 8; bit_number = bit_number + 1)
                    if (request_value[bit_number]) expected_index = bit_number;
            end
            #1;
            if (index !== old_index || valid !== old_valid) begin
                errors = errors + 1;
                if (errors <= 8) $display("FAIL outputs changed before rising clock edge");
            end
            @(posedge clk);
            #1;
            if (index !== expected_index || valid !== expected_valid) begin
                errors = errors + 1;
                if (errors <= 8)
                    $display("FAIL rst=%b request=%h expected=%b/%d got=%b/%d",
                             rst, request, expected_valid, expected_index, valid, index);
            end
        end
    endtask

    initial begin
        // Establish reset at a rising edge before checking between-edge holds.
        repeat (2) @(posedge clk);
        #1;
        if (index !== 0 || valid !== 0) begin
            errors = errors + 1;
            $display("FAIL initial reset outputs");
        end
        // Exhaust every input, including zero, one-hot and simultaneous requests.
        for (pattern = 0; pattern < 256; pattern = pattern + 1)
            check_cycle(0, pattern);
        // Assert reset away from the active edge while both outputs are nonzero.
        check_cycle(0, 8'h80);
        check_cycle(1, 8'hff);
        check_cycle(1, 8'h01);
        check_cycle(0, 8'h00);
        // Reverse order exposes stale-output and previous-input dependencies.
        for (pattern = 255; pattern >= 0; pattern = pattern - 1)
            check_cycle(0, pattern);
        if (errors == 0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end

    initial begin
        #10000;
        $display("TEST FAILED: watchdog");
        $finish;
    end
endmodule
