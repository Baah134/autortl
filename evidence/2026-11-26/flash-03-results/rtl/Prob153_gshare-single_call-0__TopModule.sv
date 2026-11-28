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

    // 7-bit global branch history register
    reg [6:0] history_reg;

    // 128-entry table of 2-bit saturating counters (PHT)
    // 2'b00: Strongly Not Taken, 2'b01: Weakly Not Taken
    // 2'b10: Weakly Taken,     2'b11: Strongly Taken
    reg [1:0] pht [0:127];

    // Hashed index for prediction
    wire [6:0] predict_index = predict_pc ^ history_reg;

    // Hashed index for training
    wire [6:0] train_index = train_pc ^ train_history;

    // Prediction interface outputs
    assign predict_history = history_reg;
    assign predict_taken   = pht[predict_index][1]; // MSB determines taken / not taken

    // Global History Register update logic:
    // When a branch prediction is requested (predict_valid = 1), history updates with predicted direction:
    //   new_history = {history_reg[5:0], predict_taken}
    // When a misprediction is trained (train_valid & train_mispredicted), recover history to state
    // immediately after the mispredicting branch completes execution:
    //   recovered_history = {train_history[5:0], train_taken}
    // Training takes precedence over prediction when both occur in the same cycle.
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            history_reg <= 7'b0;
        end else begin
            if (train_valid && train_mispredicted) begin
                history_reg <= {train_history[5:0], train_taken};
            end else if (predict_valid) begin
                history_reg <= {history_reg[5:0], predict_taken};
            end
        end
    end

    // Pattern History Table (PHT) update logic:
    // 2-bit saturating counter increments on taken, decrements on not taken
    integer i;
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            for (i = 0; i < 128; i = i + 1) begin
                pht[i] <= 2'b01; // Initialize to weakly not taken
            end
        end else if (train_valid) begin
            if (train_taken) begin
                if (pht[train_index] != 2'b11)
                    pht[train_index] <= pht[train_index] + 2'b01;
            end else begin
                if (pht[train_index] != 2'b00)
                    pht[train_index] <= pht[train_index] - 2'b01;
            end
        end
    end

endmodule
