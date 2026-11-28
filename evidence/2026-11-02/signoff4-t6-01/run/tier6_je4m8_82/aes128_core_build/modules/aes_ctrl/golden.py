def init():
    return dict(busy=0, out_valid=0, rnd=0, ct=0, rk=0)


def step(state, inputs):
    busy = int(state.get("busy", 0))
    out_valid = int(state.get("out_valid", 0))
    rnd = int(state.get("rnd", 0))
    ct = int(state.get("ct", 0)) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    rk = int(state.get("rk", 0)) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

    rst = int(inputs.get("rst", 0))
    in_valid = int(inputs.get("in_valid", 0))
    out_ready = int(inputs.get("out_ready", 0))

    if rst:
        busy = 0
        out_valid = 0
        rnd = 0
        ct = 0
        rk = 0
    elif busy:
        rk = int(inputs.get("key_next", 0)) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        if rnd == 0:
            rnd = 1
        else:
            ct = int(inputs.get("round_out", 0)) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            if rnd == 10:
                busy = 0
                out_valid = 1
                rnd = 0
            else:
                rnd = (rnd + 1) & 0xF
    elif out_valid:
        if out_ready:
            out_valid = 0
    elif in_valid:
        key = int(inputs.get("key", 0)) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        pt = int(inputs.get("pt", 0)) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ct = (pt ^ key) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        rk = key
        rnd = 0
        busy = 1

    rcon_values = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36)
    if rnd < 10:
        rcon = rcon_values[rnd]
    else:
        rcon = 0

    state = dict(busy=busy, out_valid=out_valid, rnd=rnd, ct=ct, rk=rk)
    outputs = dict(
        in_ready=int(not busy and not out_valid),
        out_valid=out_valid,
        ct=ct,
        rk=rk,
        rcon=rcon,
        last=int(rnd == 10),
    )
    return state, outputs