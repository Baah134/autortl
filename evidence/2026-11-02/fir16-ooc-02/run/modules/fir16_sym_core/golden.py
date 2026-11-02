def init():
    unique = [-6, -20, -24, 18, 110, 226, 330, 390]
    coeffs = []
    for i in range(8):
        coeffs.append(unique[i])
    for i in range(8):
        coeffs.append(unique[7 - i])

    history = []
    for i in range(15):
        history.append(0)

    return dict(coeffs=coeffs, history=history)


def step(state, inputs):
    if inputs.get("rst", 0):
        history = []
        for i in range(15):
            history.append(0)
        return dict(coeffs=state.get("coeffs", []), history=history), dict(out_sample=0)

    raw = int(inputs.get("in_sample", 0)) & 65535
    sample = raw
    if raw >= 32768:
        sample = raw - 65536

    coeffs = state.get("coeffs", [])
    history = state.get("history", [])
    acc = coeffs[0] * sample
    for k in range(1, 16):
        acc = acc + coeffs[k] * history[k - 1]

    result = (acc + 1024) // 2048
    if result > 32767:
        result = 32767
    elif result < -32768:
        result = -32768

    next_history = [sample]
    for i in range(14):
        next_history.append(history[i])

    next_state = dict(coeffs=coeffs, history=next_history)
    return next_state, dict(out_sample=result & 65535)