def init():
    return None


def step(state, inputs: dict):
    if int(inputs.get("rst", 0)) & 1:
        return None, {"out_data": 0}

    return None, {"out_data": int(inputs.get("in_data", 0)) & 0xFF}