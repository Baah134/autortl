def init():
    return dict(queue=[])

def step(state, inputs):
    queue = state.get("queue", [])
    rst = int(inputs.get("rst", 0))

    if rst:
        queue = []
    else:
        in_ready = 1 if len(queue) < 8 else 0
        out_valid = 1 if len(queue) > 0 else 0
        accept = bool(inputs.get("in_valid", 0)) and bool(in_ready)
        remove = bool(inputs.get("out_ready", 0)) and bool(out_valid)

        if remove:
            queue.pop(0)
        if accept:
            queue.append(int(inputs.get("in_data", 0)) & 255)

    outputs = dict()
    outputs["in_ready"] = 1 if len(queue) < 8 else 0
    outputs["out_valid"] = 1 if len(queue) > 0 else 0
    outputs["out_data"] = queue[0] if len(queue) > 0 else 0
    state["queue"] = queue
    return state, outputs