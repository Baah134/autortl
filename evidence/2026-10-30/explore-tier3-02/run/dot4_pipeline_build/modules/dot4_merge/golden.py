def init():
    return dict(dot_result=0)

def step(state, inputs):
    if inputs.get("rst", 0):
        result = 0
    else:
        left_sum = inputs.get("left_sum", 0) & 131071
        right_sum = inputs.get("right_sum", 0) & 131071
        result = (left_sum + right_sum) & 262143
    state["dot_result"] = result
    outputs = dict(dot_result=result)
    return state, outputs