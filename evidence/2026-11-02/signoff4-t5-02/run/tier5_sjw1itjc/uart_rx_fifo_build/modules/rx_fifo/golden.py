def init():
    return dict(queue=[], overflow=0, depth=4)

def step(state, inputs):
    queue = state.get("queue", []).copy()
    overflow = state.get("overflow", 0)
    depth = state.get("depth", 4)

    if inputs.get("rst", 0):
        queue = []
        overflow = 0
    else:
        count = len(queue)
        pop = bool(inputs.get("out_ready", 0)) and count != 0
        wr_en = bool(inputs.get("wr_en", 0))
        push = wr_en and (count < depth or pop)

        if pop:
            queue.pop(0)
        if push:
            queue.append(int(inputs.get("wr_data", 0)) & 255)

        overflow = int(wr_en and not push)

    outputs = dict(
        out_data=queue[0] if len(queue) != 0 else 0,
        out_valid=int(len(queue) != 0),
        overflow=overflow
    )
    return dict(queue=queue, overflow=overflow, depth=depth), outputs