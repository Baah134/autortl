def init():
    return {
        "busy": 0,
        "out_valid": 0,
        "rnd": 0,
        "ct": 0,
        "rk": 0,
    }


def step(state, inputs):
    mask = (1 << 128) - 1

    busy = state.get("busy", 0)
    out_valid = state.get("out_valid", 0)
    rnd = state.get("rnd", 0)
    ct = state.get("ct", 0) & mask
    rk = state.get("rk", 0) & mask

    if inputs.get("rst", 0):
        busy = 0
        out_valid = 0
        rnd = 0
        ct = 0
        rk = 0
    elif busy:
        rk = inputs.get("key_next", 0) & mask
        if rnd == 0:
            rnd = 1
        else:
            ct = inputs.get("round_out", 0) & mask
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
        ct = (inputs.get("pt", 0) ^ inputs.get("key", 0)) & mask
        rk = inputs.get("key", 0) & mask
        rnd = 0
        busy = 1

    state["busy"] = busy
    state["out_valid"] = out_valid
    state["rnd"] = rnd
    state["ct"] = ct
    state["rk"] = rk

    rcon_values = (1, 2, 4, 8, 16, 32, 64, 128, 27, 54)
    rcon = rcon_values[rnd] if rnd < 10 else 0

    outputs = {
        "in_ready": int(not busy and not out_valid),
        "out_valid": out_valid,
        "ct": ct,
        "rk": rk,
        "rcon": rcon,
        "last": int(rnd == 10),
    }
    return state, outputs