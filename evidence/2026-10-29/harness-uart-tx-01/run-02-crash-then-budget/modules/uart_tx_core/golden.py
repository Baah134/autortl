def init():
    return dict(busy=0, data=0, bit_index=0, count=0, div=868, tx=1, in_ready=1)

def step(state, inputs):
    rst = int(inputs.get("rst", 0))
    div = int(inputs.get("DIV", state.get("div", 868)))

    if rst:
        state["busy"] = 0
        state["data"] = 0
        state["bit_index"] = 0
        state["count"] = 0
        state["div"] = div
        state["tx"] = 1
        state["in_ready"] = 1
    elif state.get("busy", 0):
        state["div"] = div
        if state["count"] == 1:
            if state["bit_index"] == 9:
                state["busy"] = 0
                state["bit_index"] = 0
                state["count"] = 0
                state["tx"] = 1
                state["in_ready"] = 1
            else:
                state["bit_index"] = state["bit_index"] + 1
                state["count"] = div
                if state["bit_index"] <= 8:
                    state["tx"] = (state["data"] >> (state["bit_index"] - 1)) & 1
                else:
                    state["tx"] = 1
        else:
            state["count"] = state["count"] - 1
    elif int(inputs.get("in_valid", 0)) and int(state.get("in_ready", 1)):
        state["busy"] = 1
        state["data"] = int(inputs.get("in_data", 0)) & 255
        state["bit_index"] = 0
        state["count"] = div
        state["div"] = div
        state["tx"] = 0
        state["in_ready"] = 0
    else:
        state["div"] = div

    outputs = dict(in_ready=int(state["in_ready"]), tx=int(state["tx"]))
    return state, outputs