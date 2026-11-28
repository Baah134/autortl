def init():
    return dict(queue=[])

def step(state, inputs):
    queue = state.get("queue", []).copy()
    rst = int(inputs.get("rst", 0)) & 1

    if rst:
        queue = []
    else:
        in_ready = int(len(queue) < 8)
        out_valid = int(len(queue) > 0)
        enqueue = in_ready and (int(inputs.get("in_valid", 0)) & 1)
        dequeue = out_valid and (int(inputs.get("out_ready", 0)) & 1)

        if dequeue:
            queue.pop(0)
        if enqueue:
            queue.append(int(inputs.get("in_data", 0)) & 255)

    outputs = dict(
        in_ready=int(len(queue) < 8),
        out_data=queue[0] if len(queue) > 0 else 0,
        out_valid=int(len(queue) > 0)
    )
    return dict(queue=queue), outputs