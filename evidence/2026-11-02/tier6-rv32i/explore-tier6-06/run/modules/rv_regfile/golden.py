def init():
    return dict(x=list([0] * 32), rdata1=0, rdata2=0)

def step(state, inputs):
    if inputs.get("rst", 0):
        state["x"] = list([0] * 32)
        state["rdata1"] = 0
        state["rdata2"] = 0
    else:
        raddr1 = int(inputs.get("raddr1", 0)) & 31
        raddr2 = int(inputs.get("raddr2", 0)) & 31
        state["rdata1"] = state["x"][raddr1] if raddr1 != 0 else 0
        state["rdata2"] = state["x"][raddr2] if raddr2 != 0 else 0
        waddr = int(inputs.get("waddr", 0)) & 31
        if inputs.get("we", 0) and waddr != 0:
            state["x"][waddr] = int(inputs.get("wdata", 0)) & 4294967295
    outputs = dict(rdata1=state["rdata1"], rdata2=state["rdata2"])
    return state, outputs