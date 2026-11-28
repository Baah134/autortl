def init():
    return dict(last=3, grant=0, wr_en=0, wr_addr=0, wr_data=0)


def step(state, inputs):
    if inputs.get("rst", 0):
        state["last"] = 3
        state["grant"] = 0
        state["wr_en"] = 0
        state["wr_addr"] = 0
        state["wr_data"] = 0
    else:
        req = int(inputs.get("req", 0)) & 15
        last = int(state.get("last", 3)) & 3
        winner = -1

        for offset in range(1, 5):
            index = (last + offset) & 3
            if req & (1 << index):
                winner = index
                break

        if winner >= 0:
            addresses = [
                int(inputs.get("addr0", 0)) & 7,
                int(inputs.get("addr1", 0)) & 7,
                int(inputs.get("addr2", 0)) & 7,
                int(inputs.get("addr3", 0)) & 7,
            ]
            data = [
                int(inputs.get("data0", 0)) & 255,
                int(inputs.get("data1", 0)) & 255,
                int(inputs.get("data2", 0)) & 255,
                int(inputs.get("data3", 0)) & 255,
            ]
            state["grant"] = 1 << winner
            state["wr_en"] = 1
            state["wr_addr"] = addresses[winner]
            state["wr_data"] = data[winner]
            state["last"] = winner
        else:
            state["grant"] = 0
            state["wr_en"] = 0
            state["wr_addr"] = 0
            state["wr_data"] = 0

    outputs = dict(
        grant=int(state.get("grant", 0)) & 15,
        wr_en=int(state.get("wr_en", 0)) & 1,
        wr_addr=int(state.get("wr_addr", 0)) & 7,
        wr_data=int(state.get("wr_data", 0)) & 255,
    )
    return state, outputs