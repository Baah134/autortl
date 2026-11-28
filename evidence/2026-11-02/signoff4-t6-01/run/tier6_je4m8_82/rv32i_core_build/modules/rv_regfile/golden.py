def init():
    return dict(x=[0] * 32, rdata1=0, rdata2=0)


def step(state, inputs):
    if int(inputs.get("rst", 0)) & 1:
        for i in range(1, 32):
            state["x"][i] = 0
        state["rdata1"] = 0
        state["rdata2"] = 0
    else:
        raddr1 = int(inputs.get("raddr1", 0)) & 31
        raddr2 = int(inputs.get("raddr2", 0)) & 31
        state["rdata1"] = state["x"][raddr1] & 4294967295
        state["rdata2"] = state["x"][raddr2] & 4294967295

        waddr = int(inputs.get("waddr", 0)) & 31
        if (int(inputs.get("we", 0)) & 1) and waddr != 0:
            state["x"][waddr] = int(inputs.get("wdata", 0)) & 4294967295

    outputs = dict(
        rdata1=state["rdata1"] & 4294967295,
        rdata2=state["rdata2"] & 4294967295
    )
    return state, outputs