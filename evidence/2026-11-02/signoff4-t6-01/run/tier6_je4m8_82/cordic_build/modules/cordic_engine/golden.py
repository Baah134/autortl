def init():
    return dict(busy=0, out_valid=0, i=0, x=0, y=0, z=0)


def step(state, inputs):
    if inputs.get("rst", 0):
        state["busy"] = 0
        state["out_valid"] = 0
        state["i"] = 0
        state["x"] = 0
        state["y"] = 0
        state["z"] = 0
    elif state["busy"]:
        i = state["i"]
        x = state["x"]
        y = state["y"]
        z = state["z"]
        atan_val = inputs.get("atan_val", 0) & 1048575

        if x & 131072:
            signed_x = x - 262144
        else:
            signed_x = x
        if y & 131072:
            signed_y = y - 262144
        else:
            signed_y = y

        xs = signed_x >> i
        ys = signed_y >> i

        if z & 524288:
            state["x"] = (x + ys) & 262143
            state["y"] = (y - xs) & 262143
            state["z"] = (z + atan_val) & 1048575
        else:
            state["x"] = (x - ys) & 262143
            state["y"] = (y + xs) & 262143
            state["z"] = (z - atan_val) & 1048575

        state["i"] = (i + 1) & 15
        if i == 15:
            state["busy"] = 0
            state["out_valid"] = 1
    elif state["out_valid"]:
        if inputs.get("out_ready", 0):
            state["out_valid"] = 0
    elif inputs.get("in_valid", 0):
        state["x"] = inputs.get("x0", 0) & 262143
        state["y"] = 0
        state["z"] = inputs.get("z0", 0) & 1048575
        state["i"] = 0
        state["busy"] = 1

    outputs = dict(
        in_ready=int(not state["busy"] and not state["out_valid"]),
        iter=state["i"] & 15,
        out_valid=state["out_valid"],
        x=state["x"] & 262143,
        y=state["y"] & 262143,
    )
    return state, outputs