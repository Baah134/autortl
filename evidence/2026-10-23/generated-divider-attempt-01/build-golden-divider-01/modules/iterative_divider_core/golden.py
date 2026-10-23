def init():
    return {}


def step(state, inputs: dict):
    mask = (1 << 8) - 1

    if inputs.get("rst", 0):
        return init(), {"quotient": 0, "remainder": 0}

    dividend = inputs.get("dividend", 0) & mask
    divisor = inputs.get("divisor", 0) & mask

    if divisor == 0:
        quotient = mask
        remainder = dividend
    else:
        quotient = dividend // divisor
        remainder = dividend % divisor

    return state, {
        "quotient": quotient & mask,
        "remainder": remainder & mask,
    }