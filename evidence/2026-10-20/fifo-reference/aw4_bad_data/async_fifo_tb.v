`timescale 1ns/1ps
// AW is replaced only by the fixture writer; DUT internals are never referenced.
module async_fifo_tb;
    localparam AW = 4;
    localparam DW = 8;
    localparam DEPTH = (1 << AW);
    reg wr_clk = 0, rd_clk = 0;
    reg wr_rst = 1, rd_rst = 1, wr_en = 0, rd_en = 0;
    reg [DW-1:0] wr_data = 0;
    wire [DW-1:0] rd_data;
    wire full, empty;
    reg [DW-1:0] expected [0:8191];
    reg [DW-1:0] read_expected, held_data;
    reg read_known = 0;
    reg [31:0] wr_random = 32'h1837ab12, rd_random = 32'h9e3779b9;
    integer write_mode = 0, read_mode = 0;
    integer written = 0, read_count = 0, errors = 0, rounds, saved_count, deadline;

    async_fifo #(.DW(DW), .AW(AW)) dut (
        .wr_clk(wr_clk), .wr_rst(wr_rst), .wr_en(wr_en), .wr_data(wr_data), .full(full),
        .rd_clk(rd_clk), .rd_rst(rd_rst), .rd_en(rd_en), .rd_data(rd_data), .empty(empty));
    always #5 wr_clk = ~wr_clk;
    // Half-nanosecond offset keeps queue updates on different simulation times.
    initial begin #0.5; forever #7 rd_clk = ~rd_clk; end

    function [31:0] next_random;
        input [31:0] state;
        reg [31:0] value;
        begin
            value = state ^ (state << 13);
            value = value ^ (value >> 17);
            next_random = value ^ (value << 5);
        end
    endfunction

    always @(negedge wr_clk) begin
        wr_random = next_random(wr_random);
        wr_en = !wr_rst && (write_mode == 1 || (write_mode == 2 && wr_random[0]));
        wr_data = wr_random[7:0]; // changing blocked writes must not overwrite memory
    end
    always @(negedge rd_clk) begin
        rd_random = next_random(rd_random);
        rd_en = !rd_rst && (read_mode == 1 || (read_mode == 2 && rd_random[1]));
    end

    always @(posedge wr_clk) begin
        if (wr_rst) written = 0;
        else begin
            if (full !== 1'b0 && full !== 1'b1) begin
                $display("FAIL unknown full"); errors = errors + 1;
            end
            if (wr_en && full === 1'b0) begin
                if (written - read_count >= DEPTH || written >= 8192) begin
                    $display("FAIL write accepted beyond capacity"); errors = errors + 1;
                end else expected[written] = wr_data;
                written = written + 1;
            end
        end
    end

    always @(posedge rd_clk) begin
        if (rd_rst) begin read_count = 0; read_known = 0; end
        else begin
            if (empty !== 1'b0 && empty !== 1'b1) begin
                $display("FAIL unknown empty"); errors = errors + 1;
            end
            if (rd_en && empty === 1'b0) begin
                if (read_count >= written || read_count >= 8192) begin
                    $display("FAIL read accepted without queued data"); errors = errors + 1;
                    read_expected = 0;
                end else read_expected = expected[read_count];
                read_count = read_count + 1;
                #1;
                if (rd_data !== read_expected) begin
                    $display("FAIL read=%0d expected=%h actual=%h", read_count, read_expected, rd_data);
                    errors = errors + 1;
                end
                read_known = 1; held_data = rd_data;
            end else if (read_known) begin
                #1;
                if (rd_data !== held_data) begin
                    $display("FAIL rejected/disabled read changed output"); errors = errors + 1;
                end
            end
        end
    end

    task reset_both;
        begin
            write_mode = 0; read_mode = 0;
            @(negedge wr_clk); wr_rst = 1;
            @(negedge rd_clk); rd_rst = 1;
            repeat (4) @(posedge wr_clk);
            repeat (4) @(posedge rd_clk);
            @(negedge wr_clk); wr_rst = 0;
            @(negedge rd_clk); rd_rst = 0;
            #2;
            if (full !== 0 || empty !== 1) begin
                $display("FAIL reset flags"); errors = errors + 1;
            end
        end
    endtask

    task fill_and_drain;
        integer start_written;
        begin
            read_mode = 0; write_mode = 1;
            start_written = written;
            deadline = 0;
            while (written < start_written + DEPTH && deadline < DEPTH + 20) begin
                @(posedge wr_clk); #2; deadline = deadline + 1;
            end
            if (written != start_written + DEPTH || full !== 1'b1) begin
                $display("FAIL FIFO did not accept exactly its capacity"); errors = errors + 1;
            end
            saved_count = written;
            repeat (8) @(posedge wr_clk);
            #2;
            if (written != saved_count) begin
                $display("FAIL blocked write accepted"); errors = errors + 1;
            end
            write_mode = 0;
            @(negedge wr_clk); #1; // let falling-edge driver disable writes
            read_mode = 1; deadline = 0;
            while (read_count < written && deadline < DEPTH + 30) begin
                @(posedge rd_clk); #2; deadline = deadline + 1;
            end
            repeat (6) @(posedge rd_clk);
            #2;
            if (read_count != written || empty !== 1'b1) begin
                $display("FAIL FIFO drain or empty read rejection"); errors = errors + 1;
            end
            read_mode = 0;
            @(negedge rd_clk); #1;
        end
    endtask

    initial begin
        reset_both;
        for (rounds = 0; rounds < 8; rounds = rounds + 1) fill_and_drain;
        write_mode = 2; read_mode = 2;
        repeat (800) @(posedge wr_clk);
        #2; write_mode = 0;
        @(negedge wr_clk); #1;
        read_mode = 1; deadline = 0;
        while (read_count < written && deadline < DEPTH + 30) begin
            @(posedge rd_clk); #2; deadline = deadline + 1;
        end
        repeat (6) @(posedge rd_clk);
        #2;
        if (written != read_count || empty !== 1'b1) begin
            $display("FAIL final randomized drain"); errors = errors + 1;
        end
        reset_both;
        fill_and_drain;
        if (errors == 0) $display("TEST PASSED");
        else $display("TEST FAILED: %0d errors", errors);
        $finish;
    end
    initial begin #100000; $display("TEST FAILED: FIFO watchdog"); $finish; end
endmodule
