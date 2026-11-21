`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire [255:0] in,
    input  wire [7:0]   sel,
    output wire         out
);

    function mux16;
        input [15:0] data;
        input [3:0]  select;
        reg [3:0] group_out;
        reg low_half;
        reg high_half;
        begin
            group_out[0] = data[ 3: 0] >> select[1:0];
            group_out[1] = data[ 7: 4] >> select[1:0];
            group_out[2] = data[11: 8] >> select[1:0];
            group_out[3] = data[15:12] >> select[1:0];

            low_half  = select[2] ? group_out[1] : group_out[0];
            high_half = select[2] ? group_out[3] : group_out[2];
            mux16     = select[3] ? high_half : low_half;
        end
    endfunction

    (* keep = "true" *) wire [15:0] bank_out;

    genvar bank;
    generate
        for (bank = 0; bank < 16; bank = bank + 1) begin : gen_bank
            assign bank_out[bank] = mux16(in[16*bank +: 16], sel[3:0]);
        end
    endgenerate

    assign out = mux16(bank_out, sel[7:4]);

endmodule