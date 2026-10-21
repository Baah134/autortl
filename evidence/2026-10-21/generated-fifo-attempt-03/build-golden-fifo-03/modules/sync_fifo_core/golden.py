def init():
    return 0


def step(state, inputs: dict):
    if int(inputs.get("rst", 0)):
        return 0, {"out_data": 0}

    out_data = int(inputs.get("in_data", 0)) & 255
    return state, {"out_data": out_data}