def init():
    return dict(h0=0, h1=0, h2=0)

def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state["h0"] = 0
        state["h1"] = 0
        state["h2"] = 0
        outputs["out_data"] = 0
    else:
        x = int(inputs.get("x", 0)) & 255
        if x >= 128:
            x = x - 256
        y = 3 * x - 5 * state["h0"] + 7 * state["h1"] - 2 * state["h2"]
        state["h2"] = state["h1"]
        state["h1"] = state["h0"]
        state["h0"] = x
        outputs["out_data"] = y & 8191
    return state, outputs