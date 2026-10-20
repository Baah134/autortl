def init():
    return {"count": 0}


def step(state, inputs: dict):
    if inputs["rst"] & 1:
        count = 0
    elif inputs["enable"] & 1:
        count = (state["count"] + 1) & 0xFF
    else:
        count = state["count"] & 0xFF

    new_state = {"count": count}
    outputs = {"count": count}
    return new_state, outputs