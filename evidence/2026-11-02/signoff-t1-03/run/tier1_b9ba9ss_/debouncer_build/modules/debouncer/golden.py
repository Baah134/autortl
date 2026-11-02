def init():
    return dict(clean=0, candidate=0, count=0)

def step(state, inputs):
    clean = state.get("clean", 0) & 1
    candidate = state.get("candidate", 0) & 1
    count = state.get("count", 0)

    if inputs.get("rst", 0) & 1:
        clean = 0
        candidate = 0
        count = 0
    else:
        noisy = inputs.get("noisy", 0) & 1
        if noisy == clean:
            count = 0
        else:
            if count > 0 and noisy == candidate:
                count = count + 1
            else:
                candidate = noisy
                count = 1
            if count >= 8:
                clean = noisy
                count = 0

    state["clean"] = clean
    state["candidate"] = candidate
    state["count"] = count
    outputs = dict(clean=clean & 1)
    return state, outputs