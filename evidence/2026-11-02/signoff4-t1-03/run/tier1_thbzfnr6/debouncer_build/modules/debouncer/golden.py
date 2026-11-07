def init():
    return dict(candidate=0, count=0, clean=0)

def step(state, inputs):
    if int(inputs.get("rst", 0)) & 1:
        state["candidate"] = 0
        state["count"] = 0
        state["clean"] = 0
    else:
        noisy = int(inputs.get("noisy", 0)) & 1
        if noisy != state["candidate"]:
            state["candidate"] = noisy
            state["count"] = 1
        elif state["count"] < 8:
            state["count"] += 1
        if state["count"] == 8 and state["candidate"] != state["clean"]:
            state["clean"] = state["candidate"]
    outputs = dict(clean=state["clean"] & 1)
    return state, outputs