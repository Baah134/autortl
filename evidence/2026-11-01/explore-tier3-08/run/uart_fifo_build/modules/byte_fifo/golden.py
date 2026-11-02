def init():
    return dict(queue=[])

def step(state, inputs):
    queue = state.get("queue", []).copy()

    if inputs.get("rst", 0):
        queue = []
    else:
        in_ready = int(len(queue) < 8)
        out_valid = int(len(queue) > 0)

        if out_valid and inputs.get("out_ready", 0):
            queue.pop(0)

        if in_ready and inputs.get("in_valid", 0):
            queue.append(inputs.get("in_data", 0) & 255)

    outputs = dict()
    outputs["in_ready"] = int(len(queue) < 8)
    outputs["out_valid"] = int(len(queue) > 0)
    outputs["out_data"] = queue[0] if len(queue) > 0 else 0
    return dict(queue=queue), outputs