`timescale 1ns/1ps
// @latency 1
module uart_tx #(
    parameter DIV = 868
) (
    input wire clk,
    input wire rst,
    input wire [7:0] data,
    output reg tx
);

    localparam [1:0] IDLE  = 2'd0;
    localparam [1:0] START = 2'd1;
    localparam [1:0] DATA  = 2'd2;
    localparam [1:0] STOP  = 2'd3;

    reg [1:0] state;
    reg [7:0] shift_data;
    reg [2:0] bit_index;
    integer bit_count;

    always @(posedge clk) begin
        if (rst) begin
            state     <= IDLE;
            tx        <= 1'b1;
            shift_data <= 8'd0;
            bit_index <= 3'd0;
            bit_count <= 0;
        end else begin
            case (state)
                IDLE: begin
                    shift_data <= data;
                    bit_index  <= 3'd0;
                    bit_count  <= DIV - 1;
                    tx         <= 1'b0;
                    state      <= START;
                end

                START: begin
                    if (bit_count != 0) begin
                        tx         <= shift_data[0];
                        shift_data <= {1'b0, shift_data[7:1]};
                        bit_index  <= 3'd0;
                        bit_count  <= DIV - 1;
                        state      <= DATA;
                    end else begin
                        bit_count <= bit_count - 1;
                    end
                end

                DATA: begin
                    if (bit_count == 0) begin
                        bit_count <= DIV - 1;
                        if (bit_index == 3'd7) begin
                            tx    <= 1'b1;
                            state <= STOP;
                        end else begin
                            tx         <= shift_data[0];
                            shift_data <= {1'b0, shift_data[7:1]};
                            bit_index  <= bit_index + 1'b1;
                        end
                    end else begin
                        bit_count <= bit_count - 1;
                    end
                end

                STOP: begin
                    if (bit_count == 0) begin
                        shift_data <= data;
                        bit_index  <= 3'd0;
                        bit_count  <= DIV - 1;
                        tx         <= 1'b0;
                        state      <= START;
                    end else begin
                        bit_count <= bit_count - 1;
                    end
                end

                default: begin
                    state     <= IDLE;
                    tx        <= 1'b1;
                    bit_count <= 0;
                end
            endcase
        end
    end

endmodule