def init():
    return dict()


def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        outputs["out_data"] = 0
    else:
        total = (
            (int(inputs.get("a0", 0)) & 255) * (int(inputs.get("b0", 0)) & 255)
            + (int(inputs.get("a1", 0)) & 255) * (int(inputs.get("b1", 0)) & 255)
            + (int(inputs.get("a2", 0)) & 255) * (int(inputs.get("b2", 0)) & 255)
            + (int(inputs.get("a3", 0)) & 255) * (int(inputs.get("b3", 0)) & 255)
        )
        outputs["out_data"] = total & 262143
    return state, outputs