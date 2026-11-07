def init():
    return dict(ferr_count=0, ovf_count=0)


def step(state, inputs):
    if inputs.get("rst", 0):
        state["ferr_count"] = 0
        state["ovf_count"] = 0
    else:
        if inputs.get("ferr_in", 0) and state["ferr_count"] < 15:
            state["ferr_count"] = state["ferr_count"] + 1
        if inputs.get("ovf_in", 0) and state["ovf_count"] < 15:
            state["ovf_count"] = state["ovf_count"] + 1

    outputs = dict(
        ferr_count=state["ferr_count"] & 15,
        ovf_count=state["ovf_count"] & 15,
    )
    return state, outputs