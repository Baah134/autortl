def init():
    mem = []
    for i in range(64):
        mem.append(0)
    return dict(mem=mem, imem_rdata=0)


def step(state, inputs):
    rst = int(inputs.get("rst", 0)) & 1
    if rst:
        for i in range(64):
            state["mem"][i] = 0
        state["imem_rdata"] = 0
    else:
        raddr = int(inputs.get("imem_raddr", 0)) & 63
        waddr = int(inputs.get("imem_waddr", 0)) & 63
        wdata = int(inputs.get("imem_wdata", 0)) & 4294967295
        old_rdata = state["mem"][raddr]
        if int(inputs.get("imem_we", 0)) & 1:
            state["mem"][waddr] = wdata
        state["imem_rdata"] = old_rdata
    outputs = dict(imem_rdata=state["imem_rdata"] & 4294967295)
    return state, outputs