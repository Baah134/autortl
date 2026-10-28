def init():
    return dict(x1=0, x2=0, x3=0)

def step(state, inputs):
    outputs = dict()
    if int(inputs.get("rst", 0)):
        state["x1"] = 0
        state["x2"] = 0
        state["x3"] = 0
        outputs["out_data"] = 0
        return state, outputs

    x = int(inputs.get("x", 0)) & 255
    if x >= 128:
        x = x - 256

    y = 3 * x - 5 * state.get("x1", 0) + 7 * state.get("x2", 0) - 2 * state.get("x3", 0)
    outputs["out_data"] = y & 8191

    state["x3"] = state.get("x2", 0)
    state["x2"] = state.get("x1", 0)
    state["x1"] = x
    return state, outputs