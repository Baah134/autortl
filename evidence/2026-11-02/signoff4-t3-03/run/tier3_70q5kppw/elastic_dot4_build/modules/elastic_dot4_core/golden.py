def init():
    return dict()


def step(state, inputs):
    outputs = dict()

    if inputs.get("rst", 0):
        outputs["out_data"] = 0
        return state, outputs

    p0 = ((inputs.get("a0", 0) & 255) * (inputs.get("b0", 0) & 255)) & 65535
    p1 = ((inputs.get("a1", 0) & 255) * (inputs.get("b1", 0) & 255)) & 65535
    p2 = ((inputs.get("a2", 0) & 255) * (inputs.get("b2", 0) & 255)) & 65535
    p3 = ((inputs.get("a3", 0) & 255) * (inputs.get("b3", 0) & 255)) & 65535

    pair0 = (p0 + p1) & 131071
    pair1 = (p2 + p3) & 131071
    outputs["out_data"] = (pair0 + pair1) & 262143
    return state, outputs