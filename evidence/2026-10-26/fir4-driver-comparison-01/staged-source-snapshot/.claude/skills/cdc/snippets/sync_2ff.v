// Two-flop synchroniser for a single slow-changing bit (example; adapt only to a matching contract)
module sync_2ff (
    input  wire dst_clk,
    input  wire d_async,
    output wire q_sync
);
    (* ASYNC_REG = "TRUE" *) reg s1, s2;
    always @(posedge dst_clk) begin
        s1 <= d_async;
        s2 <= s1;
    end
    assign q_sync = s2;
endmodule
