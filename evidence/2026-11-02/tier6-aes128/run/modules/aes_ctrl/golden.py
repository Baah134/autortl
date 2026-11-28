def init():
    return dict(busy=0, out_valid=0, rnd=0, ct=0, rk=0)


def step(state, inputs):
    if inputs.get("rst", 0):
        state["busy"] = 0
        state["out_valid"] = 0
        state["rnd"] = 0
        state["ct"] = 0
        state["rk"] = 0
    elif state["busy"]:
        state["rk"] = inputs.get("key_next", 0) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        if state["rnd"] == 0:
            state["rnd"] = 1
        else:
            state["ct"] = inputs.get("round_out", 0) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            if state["rnd"] == 10:
                state["busy"] = 0
                state["out_valid"] = 1
                state["rnd"] = 0
            else:
                state["rnd"] = state["rnd"] + 1
    elif state["out_valid"]:
        if inputs.get("out_ready", 0):
            state["out_valid"] = 0
    elif inputs.get("in_valid", 0):
        state["ct"] = (
            (inputs.get("pt", 0) ^ inputs.get("key", 0))
            & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        state["rk"] = inputs.get("key", 0) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        state["rnd"] = 0
        state["busy"] = 1

    rcon_values = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36)
    rnd = state["rnd"]
    outputs = dict(
        in_ready=int(not state["busy"] and not state["out_valid"]),
        out_valid=state["out_valid"],
        ct=state["ct"] & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        rk=state["rk"] & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        rcon=rcon_values[rnd] if rnd < 10 else 0,
        last=int(rnd == 10),
    )
    return state, outputs