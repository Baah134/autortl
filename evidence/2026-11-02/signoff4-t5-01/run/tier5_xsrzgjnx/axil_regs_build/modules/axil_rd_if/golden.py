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
    elif not rvalid:
        if inputs.get("arvalid", 0) & 1:
            araddr = inputs.get("araddr", 0) & 63
            rvalid = 1
            if araddr & 32:
                rdata = 0
                rresp = 2
            else:
                regs_flat = inputs.get("regs_flat", 0) & ((1 << 256) - 1)
                index = (araddr >> 2) & 7
                rdata = (regs_flat >> (index * 32)) & 4294967295
                rresp = 0
    elif inputs.get("rready", 0) & 1:
        rvalid = 0

    state = dict(rvalid=rvalid, rdata=rdata, rresp=rresp)
    outputs = dict(
        arready=1 - rvalid,
        rvalid=rvalid,
        rdata=rdata,
        rresp=rresp
    )
    return state, outputs