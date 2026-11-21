`timescale 1ns/1ps
// @latency 0
module TopModule (
    input  wire       clk,
    input  wire       areset,
    input  wire       predict_valid,
    input  wire [6:0] predict_pc,
    output wire       predict_taken,
    output wire [6:0] predict_history,
    input  wire       train_valid,
    input  wire       train_taken,
    input  wire       train_mispredicted,
    input  wire [6:0] train_history,
    input  wire [6:0] train_pc
);

    reg [6:0] history;
    wire [6:0] predict_index;
    wire [6:0] train_index;
    wire [5:0] predict_row;
    wire [5:0] train_row;
    wire [1:0] bank_write;
    wire [1:0] bank_predict_taken;
    wire [1:0] bank_train_high;
    wire [1:0] bank_train_low;
    wire train_high;
    wire train_low;
    wire next_high;
    wire next_low;
    wire recover_history;

    assign predict_history = history;
    assign predict_index = predict_pc ^ history;
    assign train_index = train_pc ^ train_history;
    assign predict_row = predict_index[5:0];
    assign train_row = train_index[5:0];

    assign bank_write[0] = train_valid & ~areset & ~train_index[6];
    assign bank_write[1] = train_valid & ~areset &  train_index[6];

    assign predict_taken = bank_predict_taken[predict_index[6]];
    assign train_high = bank_train_high[train_index[6]];
    assign train_low = bank_train_low[train_index[6]];

    assign next_high = train_taken ? (train_high | train_low)
                                   : (train_high & train_low);
    assign next_low  = train_taken ? (train_high | ~train_low)
                                   : (train_high & ~train_low);

    assign recover_history = train_valid & train_mispredicted;

    always @(posedge clk or posedge areset) begin
        if (areset)
            history <= 7'b0;
        else if (recover_history)
            history <= {train_history[5:0], train_taken};
        else if (predict_valid)
            history <= {history[5:0], predict_taken};
    end

    genvar bank;
    genvar row;
    generate
        for (bank = 0; bank < 2; bank = bank + 1) begin : pht_bank
            (* ram_style = "distributed" *) reg counter_high [0:63];
            (* ram_style = "distributed" *) reg counter_low  [0:63];
            wire [63:0] valid_entries;
            wire predict_entry_valid;
            wire train_entry_valid;

            assign predict_entry_valid = valid_entries[predict_row];
            assign train_entry_valid = valid_entries[train_row];

            assign bank_predict_taken[bank] =
                predict_entry_valid & counter_high[predict_row];
            assign bank_train_high[bank] =
                train_entry_valid & counter_high[train_row];
            assign bank_train_low[bank] =
                ~train_entry_valid | counter_low[train_row];

            always @(posedge clk) begin
                if (bank_write[bank]) begin
                    counter_high[train_row] <= next_high;
                    counter_low[train_row] <= next_low;
                end
            end

            for (row = 0; row < 64; row = row + 1) begin : entry
                localparam [5:0] ROW_ADDRESS = row;
                wire entry_write;
                reg valid;

                assign entry_write =
                    bank_write[bank] & (train_row == ROW_ADDRESS);
                assign valid_entries[row] = valid;

                always @(posedge clk or posedge areset) begin
                    if (areset)
                        valid <= 1'b0;
                    else if (entry_write)
                        valid <= 1'b1;
                end
            end
        end
    endgenerate

endmodule