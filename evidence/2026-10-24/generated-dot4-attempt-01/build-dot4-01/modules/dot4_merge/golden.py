def init():
    return 0


def step(state, inputs: dict) -> (int, dict):
    if inputs.get("rst", 0) & 1:
        state = 0
    else:
        left_sum = inputs.get("left_sum", 0) & 0x1FFFF
        right_sum = inputs.get("right_sum", 0) & 0x1FFFF
        state = (left_sum + right_sum) & 0x3FFFF

    return state, {"dot_result": state}