def init():
    return dict(pair01_sum=0)

def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state["pair01_sum"] = 0
    else:
        a0 = inputs.get("a0", 0) & 255
        b0 = inputs.get("b0", 0) & 255
        a1 = inputs.get("a1", 0) & 255
        b1 = inputs.get("b1", 0) & 255
        state["pair01_sum"] = (a0 * b0 + a1 * b1) & 131071
    outputs["pair01_sum"] = state["pair01_sum"]
    return state, outputs