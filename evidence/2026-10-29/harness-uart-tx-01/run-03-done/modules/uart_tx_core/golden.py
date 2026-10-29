def init():
    return dict(DIV=868, busy=0, tx=1, in_ready=1, data=0, bit_index=0, count=0)


def step(state, inputs):
    if inputs.get("rst", 0):
        state["busy"] = 0
        state["tx"] = 1
        state["in_ready"] = 1
        state["data"] = 0
        state["bit_index"] = 0
        state["count"] = 0
    elif not state.get("busy", 0):
        if inputs.get("in_valid", 0) and state.get("in_ready", 1):
            state["data"] = int(inputs.get("in_data", 0)) & 255
            state["busy"] = 1
            state["tx"] = 0
            state["in_ready"] = 0
            state["bit_index"] = 0
            state["count"] = 0
    else:
        div = int(state.get("DIV", 868))
        if state.get("count", 0) == div - 1:
            state["count"] = 0
            if state.get("bit_index", 0) == 9:
                state["busy"] = 0
                state["tx"] = 1
                state["in_ready"] = 1
                state["bit_index"] = 0
            else:
                state["bit_index"] = state.get("bit_index", 0) + 1
                if state["bit_index"] == 9:
                    state["tx"] = 1
                else:
                    state["tx"] = (state["data"] >> (state["bit_index"] - 1)) & 1
        else:
            state["count"] = state.get("count", 0) + 1

    outputs = dict(in_ready=int(state.get("in_ready", 1)), tx=int(state.get("tx", 1)))
    return state, outputs