def init():
    return dict(queue=[])

def step(state, inputs):
    queue = state.get("queue", []).copy()
    depth = 8

    if inputs.get("rst", 0):
        queue = []
    else:
        can_accept = len(queue) < depth
        can_remove = len(queue) > 0 and inputs.get("out_ready", 0)

        if can_remove:
            queue.pop(0)

        if can_accept and inputs.get("in_valid", 0):
            queue.append(int(inputs.get("in_data", 0)) & 255)

    state["queue"] = queue
    outputs = dict()
    outputs["in_ready"] = int(len(queue) < depth)
    outputs["data_out"] = queue[0] if len(queue) > 0 else 0
    outputs["valid_out"] = int(len(queue) > 0)
    return state, outputs