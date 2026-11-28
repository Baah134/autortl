def init():
    return dict(history=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state["history"] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        outputs["out_sample"] = 0
        return state, outputs

    sample = int(inputs.get("in_sample", 0)) & 65535
    if sample >= 32768:
        sample -= 65536

    coeffs = [-6, -20, -24, 18, 110, 226, 330, 390, 390, 330, 226, 110, 18, -24, -20, -6]
    history = state.get("history", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    acc = coeffs[0] * sample
    for k in range(1, 16):
        acc += coeffs[k] * history[k - 1]

    result = (acc + 1024) // 2048
    if result > 32767:
        result = 32767
    elif result < -32768:
        result = -32768

    next_history = [sample]
    for i in range(14):
        next_history.append(history[i])
    state["history"] = next_history
    outputs["out_sample"] = result & 65535
    return state, outputs