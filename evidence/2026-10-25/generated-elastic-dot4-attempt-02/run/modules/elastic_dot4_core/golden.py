def init():
    return dict()


def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        outputs["out_data"] = 0
        return state, outputs

    a0 = int(inputs.get("a0", 0)) & 255
    b0 = int(inputs.get("b0", 0)) & 255
    a1 = int(inputs.get("a1", 0)) & 255
    b1 = int(inputs.get("b1", 0)) & 255
    a2 = int(inputs.get("a2", 0)) & 255
    b2 = int(inputs.get("b2", 0)) & 255
    a3 = int(inputs.get("a3", 0)) & 255
    b3 = int(inputs.get("b3", 0)) & 255

    outputs["out_data"] = (a0 * b0 + a1 * b1 + a2 * b2 + a3 * b3) & 262143
    return state, outputs