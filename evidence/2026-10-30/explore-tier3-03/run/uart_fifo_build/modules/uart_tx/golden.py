def init():
    return dict(phase=0, count=0, bit_index=0, data=0, tx=1)

def step(state, inputs):
    outputs = dict()
    div = int(inputs.get("DIV", 868))
    if div < 1:
        div = 1

    if inputs.get("rst", 0):
        state["phase"] = 0
        state["count"] = 0
        state["bit_index"] = 0
        state["data"] = 0
        state["tx"] = 1
    elif state["phase"] == 0:
        state["tx"] = 1
        if inputs.get("in_valid", 0):
            state["data"] = int(inputs.get("in_data", 0)) & 255
            state["phase"] = 1
            state["count"] = div - 1
            state["bit_index"] = 0
            state["tx"] = 0
    elif state["phase"] == 1:
        if state["count"] > 0:
            state["count"] -= 1
        else:
            state["phase"] = 2
            state["count"] = div - 1
            state["tx"] = (state["data"] >> state["bit_index"]) & 1
    elif state["phase"] == 2:
        if state["count"] > 0:
            state["count"] -= 1
        elif state["bit_index"] < 7:
            state["bit_index"] += 1
            state["count"] = div - 1
            state["tx"] = (state["data"] >> state["bit_index"]) & 1
        else:
            state["phase"] = 3
            state["count"] = div - 1
            state["tx"] = 1
    else:
        if state["count"] > 0:
            state["count"] -= 1
        else:
            state["phase"] = 0
            state["tx"] = 1

    outputs["tx"] = int(state["tx"]) & 1
    return state, outputs