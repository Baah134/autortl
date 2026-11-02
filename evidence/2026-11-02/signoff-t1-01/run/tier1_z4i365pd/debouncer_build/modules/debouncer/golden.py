def init():
    return dict(prev=0, count=0, clean=0)

def step(state, inputs):
    noisy = int(inputs.get("noisy", 0)) & 1
    rst = int(inputs.get("rst", 0)) & 1

    if rst:
        state["prev"] = 0
        state["count"] = 0
        state["clean"] = 0
    else:
        if noisy != state["prev"]:
            state["prev"] = noisy
            state["count"] = 1
        elif state["count"] < 8:
            state["count"] += 1

        if state["count"] == 8:
            state["clean"] = noisy

    outputs = dict(clean=state["clean"] & 1)
    return state, outputs