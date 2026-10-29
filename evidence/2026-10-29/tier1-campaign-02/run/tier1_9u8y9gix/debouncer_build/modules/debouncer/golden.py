def init():
    return dict(clean=0, candidate=0, count=0)

def step(state, inputs):
    if inputs.get("rst", 0):
        state["clean"] = 0
        state["candidate"] = 0
        state["count"] = 0
    else:
        noisy = int(inputs.get("noisy", 0)) & 1
        if noisy == state["candidate"]:
            if state["count"] < 8:
                state["count"] = state["count"] + 1
        else:
            state["candidate"] = noisy
            state["count"] = 1
        if state["count"] == 8:
            state["clean"] = state["candidate"]

    outputs = dict(clean=state["clean"] & 1)
    return state, outputs