def init():
    return dict()


def step(state, inputs):
    mask = 255
    if inputs.get("rst", 0):
        outputs = dict()
        outputs["quotient"] = 0
        outputs["remainder"] = 0
        return state, outputs

    dividend = int(inputs.get("dividend", 0)) & mask
    divisor = int(inputs.get("divisor", 0)) & mask

    outputs = dict()
    if divisor == 0:
        outputs["quotient"] = mask
        outputs["remainder"] = dividend
    else:
        outputs["quotient"] = (dividend // divisor) & mask
        outputs["remainder"] = (dividend % divisor) & mask

    return state, outputs