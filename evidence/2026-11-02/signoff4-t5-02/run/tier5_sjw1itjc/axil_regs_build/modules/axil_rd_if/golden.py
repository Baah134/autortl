def init():
    return dict(rvalid=0, rdata=0, rresp=0)


def step(state, inputs):
    rvalid = state.get("rvalid", 0) & 1
    rdata = state.get("rdata", 0) & 0xFFFFFFFF
    rresp = state.get("rresp", 0) & 3

    rst = inputs.get("rst", 0) & 1
    if rst:
        rvalid = 0
        rdata = 0
        rresp = 0
    elif (inputs.get("arvalid", 0) & 1) and not rvalid:
        addr = inputs.get("araddr", 0) & 0x3F
        rvalid = 1
        if addr & 0x20:
            rdata = 0
            rresp = 2
        else:
            index = (addr >> 2) & 7
            regs_flat = inputs.get("regs_flat", 0) & ((1 << 256) - 1)
            rdata = (regs_flat >> (32 * index)) & 0xFFFFFFFF
            rresp = 0
    elif rvalid and (inputs.get("rready", 0) & 1):
        rvalid = 0

    state["rvalid"] = rvalid
    state["rdata"] = rdata
    state["rresp"] = rresp

    outputs = dict(
        arready=1 - rvalid,
        rvalid=rvalid,
        rdata=rdata,
        rresp=rresp,
    )
    return state, outputs