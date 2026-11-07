def init():
    return dict()


def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state = init()
        outputs["out_data"] = 0
        outputs["out_last"] = 0
    else:
        outputs["out_data"] = int(inputs.get("in_data", 0)) & 255
        outputs["out_last"] = int(inputs.get("in_last", 0)) & 1
    return state, outputs