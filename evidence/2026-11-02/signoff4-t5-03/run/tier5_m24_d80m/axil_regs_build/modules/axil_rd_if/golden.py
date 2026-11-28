def init():
    return dict(rvalid=0, rdata=0, rresp=0)


def step(state, inputs):
    rvalid = state.get("rvalid", 0) & 1
    rdata = state.get("rdata", 0) & 4294967295
    rresp = state.get("rresp", 0) & 3

    if inputs.get("rst", 0) & 1:
        rvalid = 0
        rdata = 0
        rresp = 0
    elif (inputs.get("arvalid", 0) & 1) and not rvalid:
        rvalid = 1
        araddr = inputs.get("araddr", 0) & 63
        if araddr & 32:
            rdata = 0
            rresp = 2
        else:
            regs_flat = inputs.get("regs_flat", 0) & ((1 << 256) - 1)
            index = (araddr >> 2) & 7
            rdata = (regs_flat >> (32 * index)) & 4294967295
            rresp = 0
    elif rvalid and (inputs.get("rready", 0) & 1):
        rvalid = 0

    state["rvalid"] = rvalid
    state["rdata"] = rdata
    state["rresp"] = rresp

    outputs = dict(
        arready=(1 - rvalid) & 1,
        rvalid=rvalid & 1,
        rdata=rdata & 4294967295,
        rresp=rresp & 3
    )
    return state, outputs