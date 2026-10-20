def init():
    return {"index": 0, "valid": 0}


def step(state, inputs: dict) -> (dict, dict):
    if inputs.get("rst", 0) & 1:
        next_state = {"index": 0, "valid": 0}
    else:
        request = inputs.get("request", 0) & 0xFF
        index = 0
        for bit in range(7, -1, -1):
            if request & (1 << bit):
                index = bit
                break
        next_state = {"index": index & 0x7, "valid": int(request != 0)}

    outputs = {
        "index": next_state["index"] & 0x7,
        "valid": next_state["valid"] & 0x1,
    }
    return next_state, outputs