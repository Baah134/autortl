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

    reg [6:0] ghr;
    reg [1:0] pht [0:127];

    wire [6:0] predict_index = predict_pc ^ ghr;
    wire [1:0] pht_pred_entry = pht[predict_index];

    assign predict_taken   = pht_pred_entry[1];
    assign predict_history = ghr;

    wire [6:0] train_index = train_pc ^ train_history;
    wire [1:0] current_pht_train_entry = pht[train_index];
    reg  [1:0] next_pht_train_entry;

    always @(*) begin
        if (train_taken) begin
            if (current_pht_train_entry != 2'b11)
                next_pht_train_entry = current_pht_train_entry + 2'b01;
            else
                next_pht_train_entry = 2'b11;
        end else begin
            if (current_pht_train_entry != 2'b00)
                next_pht_train_entry = current_pht_train_entry - 2'b01;
            else
                next_pht_train_entry = 2'b00;
        end
    end

    integer i;
    always @(posedge clk or posedge areset) begin
        if (areset) begin
            ghr <= 7'b0;
            for (i = 0; i < 128; i = i + 1) begin
                pht[i] <= 2'b01; // weakly not taken
            end
        end else begin
            // Update Pattern History Table (PHT)
            if (train_valid) begin
                pht[train_index] <= next_pht_train_entry;
            end

            // Update Global History Register (GHR)
            if (train_valid && train_mispredicted) begin
                ghr <= {train_history[5:0], train_taken};
            end else if (predict_valid) begin
                ghr <= {ghr[5:0], predict_taken};
            end
        end
    end

endmodule
