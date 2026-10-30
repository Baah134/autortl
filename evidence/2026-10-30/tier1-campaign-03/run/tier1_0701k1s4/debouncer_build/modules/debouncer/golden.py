def init():
    return dict(clean=0, prev=0, count=0)

def step(state, inputs):
    clean = state.get("clean", 0) & 1
    prev = state.get("prev", 0) & 1
    count = state.get("count", 0)
    noisy = inputs.get("noisy", 0) & 1
    rst = inputs.get("rst", 0) & 1

    if rst:
        clean = 0
        prev = 0
        count = 0
    else:
        if noisy != prev:
            count = 1
        elif count < 8:
            count = count + 1

        if count >= 8:
            clean = noisy

        prev = noisy

    state = dict(clean=clean, prev=prev, count=count)
    outputs = dict(clean=clean)
    return state, outputs