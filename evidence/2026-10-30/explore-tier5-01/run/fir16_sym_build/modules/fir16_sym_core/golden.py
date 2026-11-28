def init():
    return dict(history=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


def step(state, inputs):
    if inputs.get("rst", 0):
        state["history"] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        return state, dict(out_sample=0)

    sample = int(inputs.get("in_sample", 0)) & 65535
    if sample >= 32768:
        sample -= 65536

    coeffs = [-6, -20, -24, 18, 110, 226, 330, 390,
              390, 330, 226, 110, 18, -24, -20, -6]
    acc = coeffs[0] * sample
    for k in range(1, 16):
        acc += coeffs[k] * state["history"][k - 1]

    rounded = (acc + 1024) // 2048
    if rounded > 32767:
        rounded = 32767
    elif rounded < -32768:
        rounded = -32768

    history = [sample]
    for value in state["history"][:14]:
        history.append(value)
    state["history"] = history

    return state, dict(out_sample=rounded & 65535)