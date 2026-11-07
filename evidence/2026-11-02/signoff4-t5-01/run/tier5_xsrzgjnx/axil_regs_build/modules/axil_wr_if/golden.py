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
    aw_full = int(state.get("aw_full", 0)) & 1
    aw_addr = int(state.get("aw_addr", 0)) & 63
    w_full = int(state.get("w_full", 0)) & 1
    w_data = int(state.get("w_data", 0)) & 0xFFFFFFFF
    w_strb = int(state.get("w_strb", 0)) & 15
    bvalid = int(state.get("bvalid", 0)) & 1
    bresp = int(state.get("bresp", 0)) & 3

    if int(inputs.get("rst", 0)) & 1:
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
            if (int(state.get("aw_addr", 0)) & 32) != 0:
                bresp = 2
            else:
                bresp = 0
        elif bvalid and (int(inputs.get("bready", 0)) & 1):
            bvalid = 0

        if (int(inputs.get("awvalid", 0)) & 1) and not (int(state.get("aw_full", 0)) & 1):
            aw_full = 1
            aw_addr = int(inputs.get("awaddr", 0)) & 63

        if (int(inputs.get("wvalid", 0)) & 1) and not (int(state.get("w_full", 0)) & 1):
            w_full = 1
            w_data = int(inputs.get("wdata", 0)) & 0xFFFFFFFF
            w_strb = int(inputs.get("wstrb", 0)) & 15

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
        awready=1 - aw_full,
        wready=1 - w_full,
        bvalid=bvalid,
        bresp=bresp,
        wr_en=int(bool(do_write and not (aw_addr & 32))),
        wr_idx=(aw_addr >> 2) & 7,
        wr_data=w_data,
        wr_strb=w_strb
    )
    return state, outputs