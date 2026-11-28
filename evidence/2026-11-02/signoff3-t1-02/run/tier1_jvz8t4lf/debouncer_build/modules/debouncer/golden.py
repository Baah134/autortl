def init():
    return dict(clean=0, count=0)

def step(state, inputs):
    clean = int(state.get("clean", 0)) & 1
    count = int(state.get("count", 0))

    if int(inputs.get("rst", 0)) & 1:
        clean = 0
        count = 0
    else:
        noisy = int(inputs.get("noisy", 0)) & 1
        if noisy == clean:
            count = 0
        else:
            count = count + 1
            if count >= 8:
                clean = noisy
                count = 0

    state["clean"] = clean
    state["count"] = count
    outputs = dict(clean=clean)
    return state, outputs