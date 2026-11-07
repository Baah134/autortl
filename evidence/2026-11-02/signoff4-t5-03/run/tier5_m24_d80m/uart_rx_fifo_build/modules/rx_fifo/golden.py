def init():
    return dict(queue=[], depth=4, overflow=0)

def step(state, inputs):
    queue = state.get("queue", [])
    depth = state.get("depth", 4)

    if inputs.get("rst", 0):
        queue = []
        overflow = 0
    else:
        pop = bool(inputs.get("out_ready", 0)) and len(queue) != 0
        if pop:
            queue.pop(0)

        wr_en = bool(inputs.get("wr_en", 0))
        push = wr_en and (len(queue) < depth or pop)
        overflow = 0

        if push:
            queue.append(int(inputs.get("wr_data", 0)) & 255)
        elif wr_en:
            overflow = 1

    state["queue"] = queue
    state["depth"] = depth
    state["overflow"] = overflow

    out_valid = int(len(queue) != 0)
    out_data = queue[0] if out_valid else 0
    outputs = dict(
        out_data=out_data & 255,
        out_valid=out_valid,
        overflow=overflow
    )
    return state, outputs