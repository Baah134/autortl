def init():
    return dict(dot_result=0)

def step(state, inputs):
    if inputs.get("rst", 0):
        state["dot_result"] = 0
    else:
        left_sum = int(inputs.get("left_sum", 0)) & 131071
        right_sum = int(inputs.get("right_sum", 0)) & 131071
        state["dot_result"] = (left_sum + right_sum) & 262143
    outputs = dict(dot_result=state.get("dot_result", 0))
    return state, outputs