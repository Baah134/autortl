def init():
    return dict(rvalid=0, rdata=0, rresp=0)

def step(state, inputs):
    rvalid = int(state.get("rvalid", 0)) & 1
    rdata = int(state.get("rdata", 0)) & 0xFFFFFFFF
    rresp = int(state.get("rresp", 0)) & 3

    rst = int(inputs.get("rst", 0)) & 1
    if rst:
        rvalid = 0
        rdata = 0
        rresp = 0
    elif int(inputs.get("arvalid", 0)) & 1 and not rvalid:
        addr = int(inputs.get("araddr", 0)) & 0x3F
        regs_flat = int(inputs.get("regs_flat", 0)) & ((1 << 256) - 1)
        rvalid = 1
        if addr & 0x20:
            rdata = 0
            rresp = 2
        else:
            index = (addr >> 2) & 7
            rdata = (regs_flat >> (index * 32)) & 0xFFFFFFFF
            rresp = 0
    elif rvalid and (int(inputs.get("rready", 0)) & 1):
        rvalid = 0

    state = dict(rvalid=rvalid, rdata=rdata, rresp=rresp)
    outputs = dict(
        arready=(1 - rvalid) & 1,
        rvalid=rvalid,
        rdata=rdata & 0xFFFFFFFF,
        rresp=rresp & 3,
    )
    return state, outputs