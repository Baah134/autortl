def init():
    return None


def step(state, inputs: dict):
    if inputs.get("rst", 0):
        return init(), {"out_data": 0, "out_last": 0}

    outputs = {
        "out_data": int(inputs.get("in_data", 0)) & 0xFF,
        "out_last": int(inputs.get("in_last", 0)) & 0x1,
    }
    return state, outputs