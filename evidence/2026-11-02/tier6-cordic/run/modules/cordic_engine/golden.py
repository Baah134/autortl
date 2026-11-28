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
        x_value = state["x"]
        y_value = state["y"]
        i_value = state["i"]
        z_value = state["z"]

        if x_value & 131072:
            x_value = x_value - 262144
        if y_value & 131072:
            y_value = y_value - 262144

        xs = x_value >> i_value
        ys = y_value >> i_value
        atan_value = int(inputs.get("atan_val", 0)) & 1048575

        if z_value & 524288:
            state["x"] = (state["x"] + ys) & 262143
            state["y"] = (state["y"] - xs) & 262143
            state["z"] = (z_value + atan_value) & 1048575
        else:
            state["x"] = (state["x"] - ys) & 262143
            state["y"] = (state["y"] + xs) & 262143
            state["z"] = (z_value - atan_value) & 1048575

        state["i"] = (i_value + 1) & 15
        if i_value == 15:
            state["busy"] = 0
            state["out_valid"] = 1
    elif state["out_valid"]:
        if inputs.get("out_ready", 0):
            state["out_valid"] = 0
    elif inputs.get("in_valid", 0):
        state["x"] = int(inputs.get("x0", 0)) & 262143
        state["y"] = 0
        state["z"] = int(inputs.get("z0", 0)) & 1048575
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