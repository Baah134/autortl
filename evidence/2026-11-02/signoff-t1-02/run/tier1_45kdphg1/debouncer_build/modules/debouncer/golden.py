def init():
    return dict(clean=0, candidate=0, count=0)

def step(state, inputs):
    rst = int(inputs.get("rst", 0)) & 1
    noisy = int(inputs.get("noisy", 0)) & 1

    if rst:
        state["clean"] = 0
        state["candidate"] = 0
        state["count"] = 0
    else:
        if state["count"] == 0 or noisy != state["candidate"]:
            state["candidate"] = noisy
            state["count"] = 1
        elif state["count"] < 8:
            state["count"] += 1

        if state["count"] == 8:
            state["clean"] = noisy

    outputs = dict(clean=state["clean"] & 1)
    return state, outputs