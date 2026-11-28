def init():
    return dict()

def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state = init()
        outputs["out_data"] = 0
    else:
        outputs["out_data"] = int(inputs.get("in_data", 0)) & 255
    return state, outputs