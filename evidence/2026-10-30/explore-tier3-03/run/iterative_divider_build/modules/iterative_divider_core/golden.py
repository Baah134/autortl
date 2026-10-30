def init():
    return dict()


def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state = dict()
        outputs["quotient"] = 0
        outputs["remainder"] = 0
    else:
        dividend = int(inputs.get("dividend", 0)) & 255
        divisor = int(inputs.get("divisor", 0)) & 255
        if divisor == 0:
            outputs["quotient"] = 255
            outputs["remainder"] = dividend
        else:
            outputs["quotient"] = (dividend // divisor) & 255
            outputs["remainder"] = (dividend % divisor) & 255
    return state, outputs