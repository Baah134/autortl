def init():
    mem = []
    for i in range(64):
        mem.append(0)
    return dict(mem=mem, rdata=0)


def step(state, inputs):
    if inputs.get("rst", 0):
        for i in range(64):
            state["mem"][i] = 0
        state["rdata"] = 0
    else:
        raddr = int(inputs.get("imem_raddr", 0)) & 63
        waddr = int(inputs.get("imem_waddr", 0)) & 63
        wdata = int(inputs.get("imem_wdata", 0)) & 4294967295
        state["rdata"] = state["mem"][raddr]
        if inputs.get("imem_we", 0):
            state["mem"][waddr] = wdata

    outputs = dict(imem_rdata=state["rdata"] & 4294967295)
    return state, outputs