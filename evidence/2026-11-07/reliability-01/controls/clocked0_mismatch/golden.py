def init():
    return {"total": 0}
def step(state, inputs):
    state["total"] = 0 if inputs.get("rst", 0) else (state["total"] + inputs.get("amount", 0)) & 255
    return state, {"total": state["total"]}
