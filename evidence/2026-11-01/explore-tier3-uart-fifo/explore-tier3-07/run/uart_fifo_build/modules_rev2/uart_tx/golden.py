def init():
    return dict(phase=0, count=0, byte=0, bit_index=0)

def step(state, inputs):
    outputs = dict()
    div = 868

    if inputs.get("rst", 0):
        state["phase"] = 0
        state["count"] = 0
        state["byte"] = 0
        state["bit_index"] = 0
        outputs["tx"] = 1
    elif state.get("phase", 0) == 0:
        state["byte"] = inputs.get("data", 0) & 255
        state["bit_index"] = 0
        state["phase"] = 1
        state["count"] = div - 1
        outputs["tx"] = 0
    elif state["count"] > 0:
        state["count"] = state["count"] - 1
        if state["phase"] == 1:
            outputs["tx"] = 0
        elif state["phase"] == 2:
            outputs["tx"] = (state["byte"] >> state["bit_index"]) & 1
        else:
            outputs["tx"] = 1
    elif state["phase"] == 1:
        state["phase"] = 2
        state["bit_index"] = 0
        state["count"] = div - 1
        outputs["tx"] = state["byte"] & 1
    elif state["phase"] == 2 and state["bit_index"] < 7:
        state["bit_index"] = state["bit_index"] + 1
        state["count"] = div - 1
        outputs["tx"] = (state["byte"] >> state["bit_index"]) & 1
    elif state["phase"] == 2:
        state["phase"] = 3
        state["count"] = div - 1
        outputs["tx"] = 1
    else:
        state["phase"] = 0
        state["count"] = 0
        outputs["tx"] = 1

    outputs["tx"] = outputs["tx"] & 1
    return state, outputs