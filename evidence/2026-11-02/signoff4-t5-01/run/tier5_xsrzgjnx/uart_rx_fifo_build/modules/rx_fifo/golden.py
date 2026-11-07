def init():
    return dict(ADDR_BITS=2, queue=[], overflow=0)

def step(state, inputs):
    addr_bits = int(inputs.get("ADDR_BITS", state.get("ADDR_BITS", 2)))
    depth = 1 << addr_bits
    queue = state.get("queue", []).copy()
    overflow = 0

    if inputs.get("rst", 0):
        queue = []
    else:
        count = len(queue)
        pop = bool(inputs.get("out_ready", 0)) and count != 0
        push = bool(inputs.get("wr_en", 0)) and (count < depth or pop)

        if pop:
            queue.pop(0)

        if push:
            queue.append(int(inputs.get("wr_data", 0)) & 255)
        elif inputs.get("wr_en", 0):
            overflow = 1

    state = dict(ADDR_BITS=addr_bits, queue=queue, overflow=overflow)
    out_valid = int(len(queue) != 0)
    out_data = queue[0] if out_valid else 0
    outputs = dict(
        out_data=out_data & 255,
        out_valid=out_valid,
        overflow=overflow
    )
    return state, outputs