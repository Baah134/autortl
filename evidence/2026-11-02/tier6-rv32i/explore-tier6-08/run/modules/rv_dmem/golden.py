def init():
    return dict(mem=[0] * 32, rdata=0)

def step(state, inputs):
    if inputs.get("rst", 0):
        state["mem"] = [0] * 32
        state["rdata"] = 0
    else:
        addr = int(inputs.get("addr", 0)) & 31
        old_data = state["mem"][addr]
        state["rdata"] = old_data
        if inputs.get("we", 0):
            state["mem"][addr] = int(inputs.get("wdata", 0)) & 4294967295
    outputs = dict(rdata=state["rdata"])
    return state, outputs