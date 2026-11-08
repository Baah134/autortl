def init():
    return dict(busy=0, out_valid=0, rnd=0, ct=0, rk=0)


def step(state, inputs):
    busy = state.get("busy", 0)
    out_valid = state.get("out_valid", 0)
    rnd = state.get("rnd", 0)
    ct = state.get("ct", 0)
    rk = state.get("rk", 0)

    if inputs.get("rst", 0):
        busy = 0
        out_valid = 0
        rnd = 0
        ct = 0
        rk = 0
    elif busy:
        rk = inputs.get("key_next", 0) & ((1 << 128) - 1)
        if rnd == 0:
            rnd = 1
        else:
            ct = inputs.get("round_out", 0) & ((1 << 128) - 1)
            if rnd == 10:
                busy = 0
                out_valid = 1
                rnd = 0
            else:
                rnd = rnd + 1
    elif out_valid:
        if inputs.get("out_ready", 0):
            out_valid = 0
    elif inputs.get("in_valid", 0):
        key = inputs.get("key", 0) & ((1 << 128) - 1)
        pt = inputs.get("pt", 0) & ((1 << 128) - 1)
        ct = (pt ^ key) & ((1 << 128) - 1)
        rk = key
        rnd = 0
        busy = 1

    state = dict(busy=busy, out_valid=out_valid, rnd=rnd, ct=ct, rk=rk)

    rcon_values = (1, 2, 4, 8, 16, 32, 64, 128, 27, 54, 0, 0, 0, 0, 0, 0)
    outputs = dict(
        in_ready=int(not busy and not out_valid),
        out_valid=out_valid,
        ct=ct & ((1 << 128) - 1),
        rk=rk & ((1 << 128) - 1),
        rcon=rcon_values[rnd],
        last=int(rnd == 10)
    )
    return state, outputs