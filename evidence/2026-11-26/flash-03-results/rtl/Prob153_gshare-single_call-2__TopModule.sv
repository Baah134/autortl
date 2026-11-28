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

    // 128-entry table of 2-bit saturating counters
    reg [1:0] pht [0:127];

    // 7-bit global branch history register
    reg [6:0] ghr;

    // Index hashing using XOR between PC and history
    wire [6:0] predict_index = predict_pc ^ ghr;
    wire [6:0] train_index   = train_pc ^ train_history;

    // 2-bit counter state: 2'b00 (strongly not taken), 2'b01 (weakly not taken),
    //                      2'b10 (weakly taken),     2'b11 (strongly taken).
    // MSB of the counter indicates the prediction.
    assign predict_taken   = pht[predict_index][1];
    assign predict_history = ghr;

    integer i;

    // PHT update logic
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            for (i = 0; i < 128; i = i + 1) begin
                pht[i] <= 2'b01; // Initialize to weakly not taken
            end
        end else if (train_valid) begin
            if (train_taken) begin
                if (pht[train_index] != 2'b11)
                    pht[train_index] <= pht[train_index] + 1'b1;
            end else begin
                if (pht[train_index] != 2'b00)
                    pht[train_index] <= pht[train_index] - 1'b1;
            end
        end
    end

    // GHR update logic
    // When train_valid and train_mispredicted are asserted, history recovers to the state
    // immediately after the mispredicting branch completes execution: {train_history[5:0], train_taken}.
    // Training misprediction takes precedence over a concurrent prediction.
    // Otherwise, if predict_valid is asserted, shift in the predicted outcome: {ghr[5:0], predict_taken}.
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            ghr <= 7'b0;
        end else begin
            if (train_valid && train_mispredicted) begin
                ghr <= {train_history[5:0], train_taken};
            end else if (predict_valid) begin
                ghr <= {ghr[5:0], predict_taken};
            end
        end
    end

endmodule
