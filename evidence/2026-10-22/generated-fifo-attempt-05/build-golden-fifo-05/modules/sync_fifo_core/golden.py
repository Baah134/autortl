def init():
    return 0


def step(state, inputs: dict) -> (object, dict):
    if inputs.get("rst", 0):
        return init(), {"out_data": 0}

    out_data = inputs.get("in_data", 0) & 0xFF
    return state, {"out_data": out_data}