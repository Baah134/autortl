def init():
    return dict(h1=0, h2=0, h3=0)

def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state["h1"] = 0
        state["h2"] = 0
        state["h3"] = 0
        outputs["out_data"] = 0
    else:
        x = int(inputs.get("x", 0)) & 255
        if x >= 128:
            x = x - 256
        y = 3 * x - 5 * state["h1"] + 7 * state["h2"] - 2 * state["h3"]
        outputs["out_data"] = y & 8191
        state["h3"] = state["h2"]
        state["h2"] = state["h1"]
        state["h1"] = x
    return state, outputs