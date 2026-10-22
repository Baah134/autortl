def init():
    return 0


def step(state, inputs: dict):
    if inputs.get("rst", 0):
        return 0, {"out_data": 0}

    return state, {"out_data": inputs.get("in_data", 0) & 0xFF}