def init():
    return dict(phase=0, count=0, tx=1, byte=0)


def step(state, inputs):
    div = int(inputs.get("DIV", state.get("DIV", 868)))
    if div < 1:
        div = 1

    if inputs.get("rst", 0):
        state["phase"] = 0
        state["count"] = 0
        state["tx"] = 1
        state["byte"] = 0
        outputs = dict(tx=1)
        return state, outputs

    phase = state.get("phase", 0)
    count = state.get("count", 0)

    if phase == 0:
        state["byte"] = int(inputs.get("data", 0)) & 255
        state["phase"] = 1
        state["count"] = 1
        state["tx"] = 0
    elif count >= div:
        if phase == 1:
            state["phase"] = 2
            state["tx"] = state.get("byte", 0) & 1
        elif phase >= 2 and phase <= 8:
            bit_index = phase - 1
            state["phase"] = phase + 1
            state["tx"] = (state.get("byte", 0) >> bit_index) & 1
        elif phase == 9:
            state["phase"] = 10
            state["tx"] = 1
        else:
            state["phase"] = 0
            state["tx"] = 1
        state["count"] = 1
    else:
        state["count"] = count + 1

    outputs = dict(tx=state.get("tx", 1) & 1)
    return state, outputs