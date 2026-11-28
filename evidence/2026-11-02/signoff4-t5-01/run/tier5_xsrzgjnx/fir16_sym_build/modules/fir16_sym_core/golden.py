def init():
    history = list()
    for i in range(15):
        history.append(0)
    return dict(history=history)

def step(state, inputs):
    outputs = dict()
    if int(inputs.get("rst", 0)):
        history = list()
        for i in range(15):
            history.append(0)
        state["history"] = history
        outputs["out_sample"] = 0
        return state, outputs

    sample = int(inputs.get("in_sample", 0)) & 65535
    if sample >= 32768:
        sample -= 65536

    history = state.get("history", list())
    acc = 0
    for k in range(16):
        if k == 0:
            value = sample
        else:
            value = history[k - 1]
        if k < 8:
            coeff = (-6, -20, -24, 18, 110, 226, 330, 390)[k]
        else:
            coeff = (-6, -20, -24, 18, 110, 226, 330, 390)[15 - k]
        acc += coeff * value

    rounded = (acc + 1024) // 2048
    if rounded > 32767:
        rounded = 32767
    elif rounded < -32768:
        rounded = -32768

    new_history = list()
    new_history.append(sample)
    for i in range(14):
        new_history.append(history[i])
    state["history"] = new_history
    outputs["out_sample"] = rounded & 65535
    return state, outputs