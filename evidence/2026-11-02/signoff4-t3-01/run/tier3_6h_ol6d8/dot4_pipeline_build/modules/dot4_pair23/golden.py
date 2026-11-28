def init():
    return dict(pair23_sum=0)

def step(state, inputs):
    if inputs.get("rst", 0):
        state["pair23_sum"] = 0
    else:
        a2 = int(inputs.get("a2", 0)) & 255
        b2 = int(inputs.get("b2", 0)) & 255
        a3 = int(inputs.get("a3", 0)) & 255
        b3 = int(inputs.get("b3", 0)) & 255
        state["pair23_sum"] = (a2 * b2 + a3 * b3) & 131071

    outputs = dict(pair23_sum=state["pair23_sum"])
    return state, outputs