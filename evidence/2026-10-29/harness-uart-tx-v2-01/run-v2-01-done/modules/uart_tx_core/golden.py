def init():
    return dict(active=0, data=0, bit_index=0, phase=0, tx=1, in_ready=1)


def step(state, inputs):
    div = 868
    stop = div - div // 16

    if inputs.get("rst", 0):
        state["active"] = 0
        state["data"] = 0
        state["bit_index"] = 0
        state["phase"] = 0
        state["tx"] = 1
        state["in_ready"] = 1
    elif state["active"]:
        state["phase"] = state["phase"] + 1
        if state["bit_index"] < 9 and state["phase"] == div:
            state["bit_index"] = state["bit_index"] + 1
            state["phase"] = 0
            if state["bit_index"] < 9:
                state["tx"] = (state["data"] >> (state["bit_index"] - 1)) & 1
            else:
                state["tx"] = 1
        elif state["bit_index"] == 9 and state["phase"] == stop:
            state["active"] = 0
            state["phase"] = 0
            state["tx"] = 1
            state["in_ready"] = 1
    elif inputs.get("in_valid", 0) and state["in_ready"]:
        state["data"] = inputs.get("in_data", 0) & 255
        state["active"] = 1
        state["bit_index"] = 0
        state["phase"] = 0
        state["tx"] = 0
        state["in_ready"] = 0

    outputs = dict(in_ready=state["in_ready"], tx=state["tx"])
    return state, outputs