// Lexical metadata fixture only; not evidence of synthesizability or simulation.
// @latency 7
module earlier(input x, output y);
    assign y=x;
endmodule

/* A quoted example must not annotate the following target:
// @latency 99
module imaginary; endmodule
*/
`timescale 1ns/1ps
module target(input x, output y);
    // @latency 2
    initial $display("module quoted_fake; // @latency 81 endmodule");
    assign y=x;
endmodule

// @latency 4
module later(input x, output y);
    assign y=x;
endmodule
