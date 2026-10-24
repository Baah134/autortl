def init():
    return 0


def step(state, inputs: dict) -> (object, dict):
    if inputs.get("rst", 0) & 1:
        state = 0
    else:
        a0 = inputs.get("a0", 0) & 0xFF
        b0 = inputs.get("b0", 0) & 0xFF
        a1 = inputs.get("a1", 0) & 0xFF
        b1 = inputs.get("b1", 0) & 0xFF
        state = (a0 * b0 + a1 * b1) & 0x1FFFF

    return state, {"pair01_sum": state}