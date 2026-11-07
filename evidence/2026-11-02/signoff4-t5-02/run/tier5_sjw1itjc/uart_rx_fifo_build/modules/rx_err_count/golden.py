def init():
    return dict(ferr_count=0, ovf_count=0)

def step(state, inputs):
    ferr_count = state.get("ferr_count", 0)
    ovf_count = state.get("ovf_count", 0)

    if int(inputs.get("rst", 0)) & 1:
        ferr_count = 0
        ovf_count = 0
    else:
        if (int(inputs.get("ferr_in", 0)) & 1) and ferr_count < 15:
            ferr_count += 1
        if (int(inputs.get("ovf_in", 0)) & 1) and ovf_count < 15:
            ovf_count += 1

    state["ferr_count"] = ferr_count
    state["ovf_count"] = ovf_count

    outputs = dict()
    outputs["ferr_count"] = ferr_count & 15
    outputs["ovf_count"] = ovf_count & 15
    return state, outputs