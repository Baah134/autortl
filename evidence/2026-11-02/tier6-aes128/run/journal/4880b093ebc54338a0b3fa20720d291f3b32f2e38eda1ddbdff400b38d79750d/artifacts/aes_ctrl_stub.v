module aes_ctrl (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [127:0] key,
    input wire [127:0] pt,
    output wire out_valid,
    input wire out_ready,
    output wire [127:0] ct,
    output wire [127:0] rk,
    output wire [7:0] rcon,
    output wire last,
    input wire [127:0] round_out,
    input wire [127:0] key_next
);
endmodule
