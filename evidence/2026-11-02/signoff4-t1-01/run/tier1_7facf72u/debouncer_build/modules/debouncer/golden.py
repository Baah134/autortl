def init():
    return dict(history=0, count=0, clean=0)

def step(state, inputs):
    rst = int(inputs.get("rst", 0)) & 1
    if rst:
        state["history"] = 0
        state["count"] = 0
        state["clean"] = 0
    else:
        noisy = int(inputs.get("noisy", 0)) & 1
        if noisy == state["history"]:
            if state["count"] < 8:
                state["count"] += 1
        else:
            state["history"] = noisy
            state["count"] = 1
        if state["count"] == 8:
            state["clean"] = noisy

    outputs = dict(clean=state["clean"] & 1)
    return state, outputs