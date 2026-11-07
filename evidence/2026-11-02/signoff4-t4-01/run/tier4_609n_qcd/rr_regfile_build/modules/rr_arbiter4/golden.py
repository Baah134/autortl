def init():
    return dict(last=3, grant=0, wr_en=0, wr_addr=0, wr_data=0)


def step(state, inputs):
    if inputs.get("rst", 0) & 1:
        state["last"] = 3
        state["grant"] = 0
        state["wr_en"] = 0
        state["wr_addr"] = 0
        state["wr_data"] = 0
    else:
        req = inputs.get("req", 0) & 15
        winner = -1
        offset = 1
        while offset <= 4:
            index = (state["last"] + offset) & 3
            if (req >> index) & 1:
                winner = index
                break
            offset += 1

        if winner >= 0:
            addresses = [
                inputs.get("addr0", 0) & 7,
                inputs.get("addr1", 0) & 7,
                inputs.get("addr2", 0) & 7,
                inputs.get("addr3", 0) & 7
            ]
            data = [
                inputs.get("data0", 0) & 255,
                inputs.get("data1", 0) & 255,
                inputs.get("data2", 0) & 255,
                inputs.get("data3", 0) & 255
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
        grant=state["grant"] & 15,
        wr_en=state["wr_en"] & 1,
        wr_addr=state["wr_addr"] & 7,
        wr_data=state["wr_data"] & 255
    )
    return state, outputs