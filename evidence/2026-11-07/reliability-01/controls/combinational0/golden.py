def init():
    return {}
def step(state, inputs):
    return state, {"total": inputs.get("amount", 0)}
