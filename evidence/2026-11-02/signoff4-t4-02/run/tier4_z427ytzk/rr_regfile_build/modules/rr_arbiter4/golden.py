def init():
    return dict(last=3, grant=0, wr_en=0, wr_addr=0, wr_data=0)


def step(state, inputs):
    if int(inputs.get("rst", 0)) & 1:
        state = dict(last=3, grant=0, wr_en=0, wr_addr=0, wr_data=0)
    else:
        req = int(inputs.get("req", 0)) & 15
        winner = -1
        for offset in range(1, 5):
            index = (state.get("last", 3) + offset) % 4
            if ((req >> index) & 1) and winner == -1:
                winner = index

        if winner == 0:
            state = dict(last=0, grant=1, wr_en=1,
                         wr_addr=int(inputs.get("addr0", 0)) & 7,
                         wr_data=int(inputs.get("data0", 0)) & 255)
        elif winner == 1:
            state = dict(last=1, grant=2, wr_en=1,
                         wr_addr=int(inputs.get("addr1", 0)) & 7,
                         wr_data=int(inputs.get("data1", 0)) & 255)
        elif winner == 2:
            state = dict(last=2, grant=4, wr_en=1,
                         wr_addr=int(inputs.get("addr2", 0)) & 7,
                         wr_data=int(inputs.get("data2", 0)) & 255)
        elif winner == 3:
            state = dict(last=3, grant=8, wr_en=1,
                         wr_addr=int(inputs.get("addr3", 0)) & 7,
                         wr_data=int(inputs.get("data3", 0)) & 255)
        else:
            state = dict(last=state.get("last", 3), grant=0, wr_en=0,
                         wr_addr=0, wr_data=0)

    outputs = dict(
        grant=state["grant"] & 15,
        wr_en=state["wr_en"] & 1,
        wr_addr=state["wr_addr"] & 7,
        wr_data=state["wr_data"] & 255
    )
    return state, outputs