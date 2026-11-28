`timescale 1 ps/1 ps
module tb();
  reg a; wire y_ref, y_dut; integer errors = 0, samples = 0, i;
  RefModule good (.a(a), .y(y_ref));
  TopModule top_module1 (.a(a), .y(y_dut));
  initial begin
    for (i = 0; i < 20; i = i + 1) begin
      a = i[0]; #5;
      samples = samples + 1;
      if (y_ref !== y_dut) errors = errors + 1;
    end
    $display("Mismatches: %0d in %0d samples", errors, samples);
    $finish;
  end
endmodule
