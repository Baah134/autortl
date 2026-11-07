def init():
    return dict(history=[0, 0, 0])

def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state["history"] = [0, 0, 0]
        outputs["out_data"] = 0
        return state, outputs

    history = state.get("history", [0, 0, 0])
    sample = int(inputs.get("x", 0)) & 255
    if sample >= 128:
        sample = sample - 256

    result = 3 * sample - 5 * history[0] + 7 * history[1] - 2 * history[2]
    state["history"] = [sample, history[0], history[1]]
    outputs["out_data"] = result & 8191
    return state, outputs