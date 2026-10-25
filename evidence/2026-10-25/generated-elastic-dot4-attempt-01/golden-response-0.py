def init():
    return None


def step(state, inputs: dict) -> (state, outputs: dict):
    if inputs.get("rst", 0) & 1:
        return state, {"out_data": 0}

    total = sum(
        (inputs.get(f"a{i}", 0) & 0xFF) * (inputs.get(f"b{i}", 0) & 0xFF)
        for i in range(4)
    )
    return state, {"out_data": total & 0x3FFFF}