def init():
    return dict()


def step(state, inputs):
    addr_bits = state.get("ADDR_BITS", inputs.get("ADDR_BITS", 2))
    depth = 1 << addr_bits
    queue = state.get("queue", []).copy()
    overflow = state.get("overflow", 0)

    if inputs.get("rst", 0):
        queue = []
        overflow = 0
    else:
        count = len(queue)
        pop = bool(inputs.get("out_ready", 0)) and count != 0
        push = bool(inputs.get("wr_en", 0)) and (count < depth or pop)

        if pop:
            queue.pop(0)
        if push:
            queue.append(inputs.get("wr_data", 0) & 255)

        overflow = int(bool(inputs.get("wr_en", 0)) and not push)

    state = {
        "ADDR_BITS": addr_bits,
        "queue": queue,
        "overflow": overflow
    }

    out_valid = int(len(queue) != 0)
    out_data = queue[0] if out_valid else 0
    outputs = {
        "out_data": out_data & 255,
        "out_valid": out_valid,
        "overflow": overflow
    }
    return state, outputs