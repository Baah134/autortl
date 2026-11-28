def init():
    return dict()


def step(state, inputs):
    outputs = dict()
    mask = 255

    if inputs.get("rst", 0):
        state = dict()
        outputs["quotient"] = 0
        outputs["remainder"] = 0
        return state, outputs

    dividend = int(inputs.get("dividend", 0)) & mask
    divisor = int(inputs.get("divisor", 0)) & mask

    if divisor == 0:
        quotient = mask
        remainder = dividend
    else:
        quotient = dividend // divisor
        remainder = dividend % divisor

    outputs["quotient"] = quotient & mask
    outputs["remainder"] = remainder & mask
    return state, outputs