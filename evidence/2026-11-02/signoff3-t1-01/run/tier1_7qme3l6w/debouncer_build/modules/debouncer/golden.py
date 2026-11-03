def init():
    return dict(clean=0, last=0, count=0, have=0)

def step(state, inputs):
    outputs = dict()
    rst = int(inputs.get("rst", 0)) & 1
    if rst:
        state["clean"] = 0
        state["last"] = 0
        state["count"] = 0
        state["have"] = 0
    else:
        noisy = int(inputs.get("noisy", 0)) & 1
        if state["have"] and noisy == state["last"]:
            state["count"] = state["count"] + 1
        else:
            state["last"] = noisy
            state["count"] = 1
            state["have"] = 1
        if state["count"] >= 8:
            state["clean"] = noisy
    outputs["clean"] = state["clean"] & 1
    return state, outputs