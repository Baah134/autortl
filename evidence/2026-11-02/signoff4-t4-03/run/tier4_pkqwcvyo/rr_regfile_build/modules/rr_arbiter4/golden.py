def init():
    return dict(last=3, grant=0, wr_en=0, wr_addr=0, wr_data=0)


def step(state, inputs):
    last = state.get("last", 3)

    if inputs.get("rst", 0):
        state["last"] = 3
        state["grant"] = 0
        state["wr_en"] = 0
        state["wr_addr"] = 0
        state["wr_data"] = 0
    else:
        req = int(inputs.get("req", 0)) & 15
        winner = -1

        for offset in range(1, 5):
            candidate = (last + offset) & 3
            if winner == -1 and ((req >> candidate) & 1):
                winner = candidate

        if winner == -1:
            state["grant"] = 0
            state["wr_en"] = 0
            state["wr_addr"] = 0
            state["wr_data"] = 0
        else:
            state["last"] = winner
            state["grant"] = (1 << winner) & 15
            state["wr_en"] = 1

            if winner == 0:
                state["wr_addr"] = int(inputs.get("addr0", 0)) & 7
                state["wr_data"] = int(inputs.get("data0", 0)) & 255
            elif winner == 1:
                state["wr_addr"] = int(inputs.get("addr1", 0)) & 7
                state["wr_data"] = int(inputs.get("data1", 0)) & 255
            elif winner == 2:
                state["wr_addr"] = int(inputs.get("addr2", 0)) & 7
                state["wr_data"] = int(inputs.get("data2", 0)) & 255
            else:
                state["wr_addr"] = int(inputs.get("addr3", 0)) & 7
                state["wr_data"] = int(inputs.get("data3", 0)) & 255

    outputs = dict(
        grant=state["grant"] & 15,
        wr_en=state["wr_en"] & 1,
        wr_addr=state["wr_addr"] & 7,
        wr_data=state["wr_data"] & 255,
    )
    return state, outputs