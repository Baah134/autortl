def init():
    return dict(dot_result=0)

def step(state, inputs):
    if inputs.get("rst", 0):
        result = 0
    else:
        left = int(inputs.get("left_sum", 0)) & 131071
        right = int(inputs.get("right_sum", 0)) & 131071
        result = (left + right) & 262143
    state["dot_result"] = result
    outputs = dict(dot_result=result)
    return state, outputs