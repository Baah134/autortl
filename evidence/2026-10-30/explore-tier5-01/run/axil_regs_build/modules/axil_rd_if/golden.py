def init():
    return dict(rvalid=0, rdata=0, rresp=0)


def step(state, inputs):
    rvalid = int(state.get("rvalid", 0)) & 1
    rdata = int(state.get("rdata", 0)) & 0xFFFFFFFF
    rresp = int(state.get("rresp", 0)) & 3

    if int(inputs.get("rst", 0)) & 1:
        rvalid = 0
        rdata = 0
        rresp = 0
    else:
        arvalid = int(inputs.get("arvalid", 0)) & 1
        rready = int(inputs.get("rready", 0)) & 1

        if arvalid and not rvalid:
            araddr = int(inputs.get("araddr", 0)) & 0x3F
            if araddr & 0x20:
                rvalid = 1
                rdata = 0
                rresp = 2
            else:
                regs_flat = int(inputs.get("regs_flat", 0)) & ((1 << 256) - 1)
                index = (araddr >> 2) & 7
                rvalid = 1
                rdata = (regs_flat >> (32 * index)) & 0xFFFFFFFF
                rresp = 0
        elif rvalid and rready:
            rvalid = 0

    state = dict(rvalid=rvalid, rdata=rdata, rresp=rresp)
    outputs = dict(
        arready=1 - rvalid,
        rvalid=rvalid,
        rdata=rdata,
        rresp=rresp
    )
    return state, outputs