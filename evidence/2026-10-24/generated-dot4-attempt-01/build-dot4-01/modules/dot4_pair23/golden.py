def init():
    return {"pair23_sum": 0}


def step(state, inputs: dict) -> tuple:
    if inputs.get("rst", 0) & 1:
        value = 0
    else:
        a2 = inputs.get("a2", 0) & 0xFF
        b2 = inputs.get("b2", 0) & 0xFF
        a3 = inputs.get("a3", 0) & 0xFF
        b3 = inputs.get("b3", 0) & 0xFF
        value = (a2 * b2 + a3 * b3) & 0x1FFFF

    next_state = {"pair23_sum": value}
    return next_state, {"pair23_sum": value}