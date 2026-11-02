def init():
    return dict(x=[0] * 32, rdata1=0, rdata2=0)

def step(state, inputs):
    if inputs.get("rst", 0):
        state["x"] = [0] * 32
        state["rdata1"] = 0
        state["rdata2"] = 0
    else:
        x = state["x"]
        raddr1 = int(inputs.get("raddr1", 0)) & 31
        raddr2 = int(inputs.get("raddr2", 0)) & 31
        state["rdata1"] = x[raddr1] & 4294967295
        state["rdata2"] = x[raddr2] & 4294967295
        if inputs.get("we", 0) and (int(inputs.get("waddr", 0)) & 31) != 0:
            waddr = int(inputs.get("waddr", 0)) & 31
            state["x"][waddr] = int(inputs.get("wdata", 0)) & 4294967295

    outputs = dict(rdata1=state["rdata1"], rdata2=state["rdata2"])
    return state, outputs