`timescale 1ns/1ps
// @latency 1
module rv_ctrl (
    input wire clk,
    input wire rst,
    input wire run,
    input wire [2:0] kind,
    input wire [2:0] funct3,
    input wire [4:0] rd,
    input wire [31:0] y,
    input wire eq,
    input wire lt,
    input wire ltu,
    input wire [31:0] rs2_val,
    input wire [31:0] dmem_rdata,
    output wire [31:0] pc,
    output wire [5:0] imem_raddr,
    output wire retire,
    output wire rf_we,
    output wire [4:0] rf_waddr,
    output wire [31:0] rf_wdata,
    output wire dmem_we,
    output wire [4:0] dmem_addr,
    output wire [31:0] dmem_wdata
);

    localparam [2:0] F = 3'd0;
    localparam [2:0] D = 3'd1;
    localparam [2:0] E = 3'd2;
    localparam [2:0] M = 3'd3;
    localparam [2:0] L = 3'd4;
    localparam [2:0] W = 3'd5;

    reg [2:0] state;
    reg [31:0] pc_q;
    reg [31:0] npc;
    reg [31:0] res;
    reg [31:0] sdata;
    reg [4:0] rd_q;
    reg wb_q;
    reg st_q;
    reg ld_q;

    reg taken;

    always @(*) begin
        taken = 1'b0;
        case (funct3)
            3'b000: taken = eq;
            3'b001: taken = ~eq;
            3'b100: taken = lt;
            3'b101: taken = ~lt;
            3'b110: taken = ltu;
            3'b111: taken = ~ltu;
            default: taken = 1'b0;
        endcase
    end

    assign pc = pc_q;
    assign imem_raddr = pc_q[7:2];
    assign retire = (state == W);
    assign rf_we = (state == W) && wb_q;
    assign rf_waddr = rd_q;
    assign rf_wdata = res;
    assign dmem_we = (state == M) && st_q;
    assign dmem_addr = res[6:2];
    assign dmem_wdata = sdata;

    always @(posedge clk) begin
        if (rst) begin
            state <= F;
            pc_q <= 32'b0;
            npc <= 32'b0;
            res <= 32'b0;
            sdata <= 32'b0;
            rd_q <= 5'b0;
            wb_q <= 1'b0;
            st_q <= 1'b0;
            ld_q <= 1'b0;
        end else begin
            case (state)
                F: begin
                    if (run)
                        state <= D;
                    else
                        state <= F;
                end
                D: begin
                    state <= E;
                end
                E: begin
                    wb_q <= (kind == 3'd0) ||
                            (kind == 3'd1) ||
                            (kind == 3'd4) ||
                            (kind == 3'd5);
                    st_q <= (kind == 3'd2);
                    ld_q <= (kind == 3'd1);
                    rd_q <= rd;
                    sdata <= rs2_val;
                    if ((kind == 3'd4) || (kind == 3'd5))
                        res <= pc_q + 32'd4;
                    else
                        res <= y;

                    if ((kind == 3'd4) || ((kind == 3'd3) && taken))
                        npc <= y;
                    else if (kind == 3'd5)
                        npc <= {y[31:1], 1'b0};
                    else
                        npc <= pc_q + 32'd4;

                    if ((kind == 3'd1) || (kind == 3'd2))
                        state <= M;
                    else
                        state <= W;
                end
                M: begin
                    if (ld_q)
                        state <= L;
                    else
                        state <= W;
                end
                L: begin
                    res <= dmem_rdata;
                    state <= W;
                end
                W: begin
                    pc_q <= npc;
                    state <= F;
                end
                default: begin
                    state <= F;
                end
            endcase
        end
    end

endmodule