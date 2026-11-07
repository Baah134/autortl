def init():
    return dict(mem=[0] * 32, rdata=0)

def step(state, inputs):
    if int(inputs.get("rst", 0)) & 1:
        state["mem"] = [0] * 32
        state["rdata"] = 0
    else:
        addr = int(inputs.get("addr", 0)) & 31
        we = int(inputs.get("we", 0)) & 1
        wdata = int(inputs.get("wdata", 0)) & 4294967295
        state["rdata"] = state["mem"][addr]
        if we:
            state["mem"][addr] = wdata

    outputs = dict(rdata=state["rdata"])
    return state, outputs