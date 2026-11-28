def init():
    return dict(ferr_count=0, ovf_count=0)


def step(state, inputs):
    ferr_count = state.get("ferr_count", 0) & 15
    ovf_count = state.get("ovf_count", 0) & 15

    if inputs.get("rst", 0):
        ferr_count = 0
        ovf_count = 0
    else:
        if inputs.get("ferr_in", 0) and ferr_count < 15:
            ferr_count = ferr_count + 1
        if inputs.get("ovf_in", 0) and ovf_count < 15:
            ovf_count = ovf_count + 1

    state = dict(ferr_count=ferr_count, ovf_count=ovf_count)
    outputs = dict(ferr_count=ferr_count, ovf_count=ovf_count)
    return state, outputs