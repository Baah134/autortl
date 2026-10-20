def init():
    return None


def step(state, inputs: dict) -> (object, dict):
    if inputs.get("rst", 0):
        return None, {"out_data": 0}

    return state, {"out_data": inputs.get("in_data", 0) & 0xFF}