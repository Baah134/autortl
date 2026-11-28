def init():
    return dict()


def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        outputs["cos_out"] = 0
        outputs["sin_out"] = 0
    else:
        x_in = int(inputs.get("x_in", 0)) & 262143
        y_in = int(inputs.get("y_in", 0)) & 262143

        if x_in & 131072:
            x_in -= 262144
        if y_in & 131072:
            y_in -= 262144

        outputs["cos_out"] = ((x_in + 2) >> 2) & 65535
        outputs["sin_out"] = ((y_in + 2) >> 2) & 65535

    return state, outputs