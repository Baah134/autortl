def init():
    return dict(
        aw_full=0,
        aw_addr=0,
        w_full=0,
        w_data=0,
        w_strb=0,
        bvalid=0,
        bresp=0
    )


def step(state, inputs):
    aw_full = state.get("aw_full", 0)
    aw_addr = state.get("aw_addr", 0) & 63
    w_full = state.get("w_full", 0)
    w_data = state.get("w_data", 0) & 4294967295
    w_strb = state.get("w_strb", 0) & 15
    bvalid = state.get("bvalid", 0)
    bresp = state.get("bresp", 0) & 3

    if inputs.get("rst", 0):
        aw_full = 0
        aw_addr = 0
        w_full = 0
        w_data = 0
        w_strb = 0
        bvalid = 0
        bresp = 0
    else:
        do_write = aw_full and w_full and not bvalid

        if do_write:
            aw_full = 0
            w_full = 0
            bvalid = 1
            if aw_addr & 32:
                bresp = 2
            else:
                bresp = 0
        elif bvalid and inputs.get("bready", 0):
            bvalid = 0

        if inputs.get("awvalid", 0) and not state.get("aw_full", 0):
            aw_full = 1
            aw_addr = inputs.get("awaddr", 0) & 63

        if inputs.get("wvalid", 0) and not state.get("w_full", 0):
            w_full = 1
            w_data = inputs.get("wdata", 0) & 4294967295
            w_strb = inputs.get("wstrb", 0) & 15

    state = dict(
        aw_full=aw_full,
        aw_addr=aw_addr,
        w_full=w_full,
        w_data=w_data,
        w_strb=w_strb,
        bvalid=bvalid,
        bresp=bresp
    )

    do_write = aw_full and w_full and not bvalid
    outputs = dict(
        awready=int(not aw_full),
        wready=int(not w_full),
        bvalid=int(bool(bvalid)),
        bresp=bresp & 3,
        wr_en=int(bool(do_write and not (aw_addr & 32))),
        wr_idx=(aw_addr >> 2) & 7,
        wr_data=w_data & 4294967295,
        wr_strb=w_strb & 15
    )
    return state, outputs