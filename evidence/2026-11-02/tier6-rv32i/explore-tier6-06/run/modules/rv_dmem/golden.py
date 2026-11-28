def init():
    return dict(mem=[0] * 32, rdata=0)


def step(state, inputs):
    outputs = dict()
    if int(inputs.get("rst", 0)) & 1:
        i = 0
        while i < 32:
            state["mem"][i] = 0
            i += 1
        state["rdata"] = 0
    else:
        addr = int(inputs.get("addr", 0)) & 31
        old_data = state["mem"][addr]
        state["rdata"] = old_data & 4294967295
        if int(inputs.get("we", 0)) & 1:
            state["mem"][addr] = int(inputs.get("wdata", 0)) & 4294967295
    outputs["rdata"] = state["rdata"] & 4294967295
    return state, outputs