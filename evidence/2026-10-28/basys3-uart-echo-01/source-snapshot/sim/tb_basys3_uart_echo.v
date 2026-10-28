`timescale 1ns / 1ps
// Streams random bytes back to back into the echo design and checks that
// each one comes back unchanged, in order, with a valid stop bit.
// A short bit period keeps the simulation fast.
module tb_basys3_uart_echo;
    localparam CPB = 16;
    localparam N   = 64;

    reg clk = 1'b0;
    always #5 clk = ~clk;

    reg  btnC = 1'b1;
    reg  rx   = 1'b1;
    wire tx;
    wire [7:0] led;

    basys3_uart_echo #(.CLKS_PER_BIT(CPB)) dut (
        .clk(clk), .btnC(btnC), .RsRx(rx), .RsTx(tx), .led(led)
    );

    reg [7:0] sent [0:N-1];
    integer errors   = 0;
    integer received = 0;
    integer i, j;

    task send_byte(input [7:0] b);
        integer k;
        begin
            rx = 1'b0;
            repeat (CPB) @(posedge clk);
            for (k = 0; k < 8; k = k + 1) begin
                rx = b[k];
                repeat (CPB) @(posedge clk);
            end
            rx = 1'b1;
            repeat (CPB) @(posedge clk);
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

    initial begin
        for (i = 0; i < N; i = i + 1) sent[i] = $random;
        sent[0] = 8'h00;
        sent[1] = 8'hFF;
        sent[2] = 8'h55;
        sent[3] = 8'hAA;

        repeat (10) @(posedge clk);
        btnC = 1'b0;
        repeat (10) @(posedge clk);

        fork
            begin : sender
                for (i = 0; i < N; i = i + 1) send_byte(sent[i]);
            end
            begin : monitor
                reg [7:0] got;
                for (j = 0; j < N; j = j + 1) begin
                    recv_byte(got);
                    if (got !== sent[j]) begin
                        $display("ERROR: byte %0d expected %02h got %02h",
                                 j, sent[j], got);
                        errors = errors + 1;
                    end
                    received = received + 1;
                end
            end
        join

        if (led !== sent[N-1]) begin
            $display("ERROR: led shows %02h, expected last byte %02h",
                     led, sent[N-1]);
            errors = errors + 1;
        end

        if (errors == 0 && received == N)
            $display("PASS: %0d bytes echoed correctly", received);
        else
            $display("FAIL: %0d errors, %0d of %0d bytes received",
                     errors, received, N);
        $finish;
    end

    initial begin
        #(CPB * 10 * 10 * (N + 8));
        $display("FAIL: timeout after %0d of %0d bytes", received, N);
        $finish;
    end
endmodule
