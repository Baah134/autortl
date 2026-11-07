def init():
    unique = [-6, -20, -24, 18, 110, 226, 330, 390]
    coeffs = []
    for k in range(8):
        coeffs.append(unique[k])
    for k in range(8):
        coeffs.append(unique[7 - k])
    history = []
    for k in range(15):
        history.append(0)
    return dict(history=history, coeffs=coeffs)


def step(state, inputs):
    history = state.get("history", [])
    coeffs = state.get("coeffs", [])

    if inputs.get("rst", 0):
        new_history = []
        for k in range(15):
            new_history.append(0)
        return dict(history=new_history, coeffs=coeffs), dict(out_sample=0)

    sample = int(inputs.get("in_sample", 0)) & 65535
    if sample >= 32768:
        sample -= 65536

    acc = coeffs[0] * sample
    for k in range(1, 16):
        acc += coeffs[k] * history[k - 1]

    result = (acc + 1024) // 2048
    if result > 32767:
        result = 32767
    elif result < -32768:
        result = -32768

    new_history = [sample]
    for k in range(14):
        new_history.append(history[k])

    return dict(history=new_history, coeffs=coeffs), dict(out_sample=result & 65535)